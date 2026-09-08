# 工具入口与最短运行路径

以下命令中的 `<skill>` 与 `<project>` 由 AI 替换为实际路径。动态产物写项目，不写 skill。Python 3.10+；完整依赖见 requirements.txt，模型可选依赖见 templates/shared/requirements.txt。

核心 CLI 是跨平台 Python 命令；除特别标注外，Windows PowerShell、Linux 和 WSL2 使用相同参数。路径由 `pathlib` 处理，含空格时用当前 shell 的引号规则包住。平台安装见 `setup-windows.md` / `setup-linux-wsl.md`。

```text
python <skill>/scripts/workflow.py init --workspace <project> --competition cumcm --year 2026
python <skill>/scripts/doctor.py --competition cumcm --workspace <project>
python <skill>/scripts/parse_problem.py <project>/problem/problem.pdf --attachments <project>/data/raw/data.xlsx --output <project>/state/problem-package.json
python <skill>/scripts/workflow.py next --workspace <project>
```

求解代码内部使用 workspace-relative path、CLI/config/manifest 定位真实文件。命令行本身可以传绝对的 `<project>` 入口；运行日志也可记录解析后的绝对路径，但交付代码不得把个人机器路径写死。

AI 按阶段参考生成实际 artifact 和 receipt。receipt JSON 最少包含 status、checks、artifacts（项目相对路径）、issues。正式比赛关键节点只记录真实 human review，不自动生成未发生的签字。

完成阶段的产物应保持不变；后续阶段扩展内容时输出新版本，不覆盖已冻结路径。共享主状态本身不列为阶段 artifact。

```text
python <skill>/scripts/workflow.py complete --workspace <project> --stage 0 --receipt <project>/state/stage-0-receipt.json
python <skill>/scripts/workflow.py rollback --workspace <project> --stage 3 --reason "模型假设变化，需重算后续结果"
python <skill>/scripts/workflow.py reconcile --workspace <project>
```

`reconcile` 只读检查主阶段账、已完成 artifact 漂移和 DAG 一致性；出现 bookkeeping-lag 时按真实历史补 receipt/complete，或回退重验，不能手工改 JSON 消灯。

## DAG 派单（Stage 2 后）

```text
python <skill>/scripts/task_dag.py init --workspace <project>
python <skill>/scripts/task_dag.py board --workspace <project>
python <skill>/scripts/task_dag.py update --workspace <project> --task TQ1-solve --status in_progress
python <skill>/scripts/task_dag.py update --workspace <project> --task TQ1-solve --status done --receipt <project>/state/tq1-receipt.json
python <skill>/scripts/task_dag.py replan --workspace <project> --tasks <project>/state/replan.json --reason "加入 baseline/proposed 对照"
python <skill>/scripts/task_dag.py invalidate --workspace <project> --task TQ1-solve --reason "Q1 求解口径变化"
python <skill>/scripts/task_dag.py check --workspace <project>
```

replan 的 tasks 文件包含 `{id,title,role,deps,writable_paths,outputs,acceptance}`；done 需不同角色复核人签名并记录产物 SHA。invalidate 级联把下游标 stale，保留历史与产物。

## 终审：官方/确定性 PDF gate

单行命令跨平台：

```text
python <skill>/scripts/pdf_audit.py <project>/paper_workspace/main.pdf --competition cumcm --render-dir <project>/paper_workspace/pages --output <project>/state/pdf-audit.json
```

`pdf_audit.py` 处理赛事页数边界、缺字/占位、作者元数据、TeX Overfull/Underfull 等；自动无 error 后仍需真实视觉复核回执才 `passed`。

## 终审：advisory 版面 lint

```text
python <skill>/scripts/check_layout.py <project>/paper_workspace/main.pdf --tex <project>/paper_workspace/main.tex --output <project>/state/layout-lint.json
```

默认检查图/表首次引用距离、图形密度、图挨图、caption 长度与目标正文厚度。`100–150` 字 caption、`21–30` 页、`2/3` 图形占比等属于上游竞赛经验，默认只产生 `hint/review`，**不会让最终 gate 因经验阈值自动失败**。只有乱码等确定性损坏，或显式传 `--hard-max-pages N` 后超限，脚本才返回失败。需要把 review 也用于本地严格 CI 时可加 `--strict-review`。

## 引用一致性

```text
python <skill>/scripts/citation_audit.py --paper <project>/paper/ --output <project>/state/citation-audit.json
```

有参考文献但正文零引用、引用未定义 key 都直接失败；未引用 bibliography 项默认 needs_review，可按需要 `--strict-unused`。

## 架构图

规范见 `references/architecture-diagram.md`。Linux/WSL2：

```bash
cp <skill>/templates/diagrams/architecture.tex <project>/paper_workspace/figures/architecture.tex
cd <project>/paper_workspace/figures
xelatex -interaction=nonstopmode -halt-on-error architecture.tex
python <skill>/scripts/diagrams/check_overlap.py architecture.pdf
```

Windows PowerShell：

```powershell
Copy-Item <skill>\templates\diagrams\architecture.tex <project>\paper_workspace\figures\architecture.tex
Set-Location <project>\paper_workspace\figures
xelatex -interaction=nonstopmode -halt-on-error architecture.tex
python <skill>\scripts\diagrams\check_overlap.py architecture.pdf
```

各问流程图使用 `templates/diagrams/flow_snake.tex` 的蛇形横向布局，不使用总体架构图模板。

## Claim / final gate

关键 headline/innovation claim 通过 `claim_registry.py` 绑定 source field、验证器、独立性报告和 SHA；证据漂移后 check 失败。`final_gate.py` 汇总 workflow、claims、citation、PDF、合规并输出 `READY/BLOCKED`。具体参数见 scripts/README.md 与 verification.md。

## 论文与语料

论文命令见 paper-tools.md；语言命令见 academic-style.md。资料库核心命令跨平台：

```text
python <skill>/scripts/corpus.py ingest --papers-dir <project>/local-corpus --manifest <project>/paper-sources.json --output <project>/corpus-index.json
python <skill>/scripts/corpus.py stats --index <project>/corpus-index.json --output <project>/corpus-statistics.json
```

上游维护脚本 `ingest_papers.py` / `download_cumcm_papers.py` 仅赛前、来源许可允许时用；不得在正式比赛自动抓取当届解题。
