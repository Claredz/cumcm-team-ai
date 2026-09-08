# 工具入口与最短运行路径

以下命令中的 <skill> 与 <project> 由 AI 替换为实际路径。动态产物写项目，不写 skill。Python 3.10+；完整依赖见 requirements.txt，模型可选依赖见 templates/shared/requirements.txt。

```bash
python <skill>/scripts/workflow.py init --workspace <project> --competition cumcm --year 2026
python <skill>/scripts/doctor.py --competition cumcm --workspace <project>
python <skill>/scripts/parse_problem.py <project>/problem/problem.pdf --attachments <project>/data/raw/data.xlsx --output <project>/state/problem-package.json
python <skill>/scripts/workflow.py next --workspace <project>
```

AI 按入口指定的阶段参考执行，生成实际 artifact 和 receipt。receipt JSON 最少包含 status（passed）、checks（真实检查描述数组）、artifacts（项目相对文件路径数组）、issues（当前未解决问题）。正式比赛的 1/3/5/9 节点还需真实 human_review：reviewer、reviewed_at、evidence。无需让用户编辑 JSON；根据实际核验结果记录，不能生成未发生的签字。

完成阶段的产物应保持不变。后续阶段扩展内容时输出新版本，例如候选题目包保存 state/stage-1/problem-package.json，语义核对后的版本保存 state/stage-2/problem-package.json；不要覆盖已完成阶段的同一路径，否则摘要检查会要求回退重验。共享主状态本身不应列为阶段 artifact。

```bash
python <skill>/scripts/workflow.py complete --workspace <project> --stage 0 --receipt <project>/state/stage-0-receipt.json
python <skill>/scripts/score_artifact.py --stage 3 --critique <project>/state/critique.json --decision-log <project>/state/decision_log.json
python <skill>/scripts/score_artifact.py --mode aggregate_qi --qi-results <project>/state/qi-results.json --decision-log <project>/state/decision_log.json
python <skill>/scripts/workflow.py rollback --workspace <project> --stage 3 --reason '模型假设变化，需重算后续结果'
python <skill>/scripts/workflow.py reconcile --workspace <project>  # 每次 autonomous 会话收尾前必跑，只读对账
```

`reconcile` 不会自动完成阶段或伪造 receipt。它只检查：主阶段账是否明显落后于盘上已有产物、已完成 artifact 是否漂移、DAG 与阶段门是否一致。出现 `bookkeeping-lag` 时按真实历史补齐 receipt/complete，或回退并重验；不能通过手工改 JSON 消灯。

## DAG 派单（Stage 2 拆解完成后启用）

任务按有向无环图派给 A/B/C，读题完成前仍按阶段推进。命令（Windows/Linux 通用，仅依赖 Python 3.10+ 标准库）：

```bash
python <skill>/scripts/task_dag.py init --workspace <project>          # 从 subproblem_dependency 生成骨架图
python <skill>/scripts/task_dag.py board --workspace <project>          # 就绪/受阻/进行中看板，按角色认领
python <skill>/scripts/task_dag.py update --workspace <project> --task TQ1-solve --status in_progress
python <skill>/scripts/task_dag.py update --workspace <project> --task TQ1-solve --status done --receipt <project>/state/tq1-receipt.json
python <skill>/scripts/task_dag.py replan --workspace <project> --tasks <project>/state/replan.json --reason 'Q2 改用两阶段模型'
python <skill>/scripts/task_dag.py invalidate --workspace <project> --task TQ1-solve --reason 'Q1 求解口径变化'
python <skill>/scripts/task_dag.py check --workspace <project>          # 已完成任务产物漂移检测
```

replan 的 tasks 文件为 `{"tasks": [{id, title, role, deps, writable_paths, outputs, acceptance}...], "cancel": ["旧任务id"]}`；新增任务缺 reviewer 时按 A→B、B→C、C→A 自动配交叉复核人。done 回执须由 ≠ 负责人角色的复核人签名（reviewer/reviewed_at/evidence/checks/artifacts），产物记录 SHA256。invalidate 会级联把全部下游标 stale（保留历史与产物，不删除）；已完成任务只能失效重做，不能取消。规范与边界见 team-workflow.md「DAG 派单模式」。

评分 schema 与合法维度见 feedback_layer1_critic.md、rubrics.md 和 tests/fixtures/，勿手填虚假分数作为检验。状态记录 SHA256；status 会报告完成后变化的产物。rollback 保留历史并标记过期，重新验证后再完成。

## 终审质量门

PDF 自动审查与视觉复核分开：

```bash
python <skill>/scripts/pdf_audit.py <project>/paper_workspace/main.pdf --competition cumcm \
  --render-dir <project>/paper_workspace/pages --output <project>/state/pdf-audit.json
```

脚本会解析同名 `.log` 中的 `Overfull/Underfull \\hbox`；最严重 Overfull >10pt 直接 error。无自动错误时状态仍为 `needs_visual_review`。真实逐页查看后记录：

```json
{"status":"passed","reviewer":"C","reviewed_at":"2026-09-08T20:00:00+08:00","evidence":"逐页查看最终 PDF 与渲染 PNG，公式/图例/表格/页边距无异常"}
```

再运行：

```bash
python <skill>/scripts/pdf_audit.py <project>/paper_workspace/main.pdf --competition cumcm \
  --render-dir <project>/paper_workspace/pages --visual-review <project>/state/visual-review.json \
  --output <project>/state/pdf-audit-final.json
```

引用一致性：

```bash
python <skill>/scripts/citation_audit.py --paper <project>/paper/ \
  --output <project>/state/citation-audit.json
```

若使用 BibTeX 可额外传 `--bibliography <project>/paper/references.bib`。有参考文献但正文零引用、引用未定义 key 都直接失败；未引用 bibliography 项默认 `needs_review`，需要时加 `--strict-unused` 作为硬门。

论文命令见 paper-tools.md。语言命令见 academic-style.md。资料库：

```bash
python <skill>/scripts/corpus.py ingest --papers-dir <project>/local-corpus --manifest <project>/paper-sources.json --output <project>/corpus-index.json
python <skill>/scripts/corpus.py stats --index <project>/corpus-index.json --output <project>/corpus-statistics.json
```

source manifest 为 {"papers":[{"filename":"2024-A163.pdf","year":2024,"topic":"A","url":"原文来源","usage_basis":"实际访问分析依据"}]}。导入去重，剔除来源缺失、扫描/短文、提取乱码；各子集独立记录样本量，空子集不给虚构分位。data/papers/README.md 解释已打包数据的边界。

上游工具 scripts/ingest_papers.py 和 download_cumcm_papers.py 保留供离线维护，完整参数见 scripts/README.md。不得在正式比赛自动抓取当届解题；不默认把下载的论文公开提交。
