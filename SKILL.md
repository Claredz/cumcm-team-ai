---
name: cumcm-team-ai
description: 数学建模全流程 skill，覆盖 CUMCM 国赛、MCM/ICM 与电工杯的题面解析、结构扫描、模型选型、三人 DAG 并行求解、稳健性、论文写作与编译、PDF/引用/结果审计和最终交付。默认建模原则优先、自动推进，核心学术判断与最终成果保留队员核验。
---

# 数学建模全流程 · cumcm-team-ai v2

## 建模宪法：先决定什么是好模型，再决定怎么跑项目

进入任何 workflow/state/tool 之前，先读 [modeling-constitution.md](references/modeling-constitution.md)。本 skill 的最高层默认是：

1. **忠于题目与官方口径**：先建立 problem contract，题面定义、单位、约束和输出要求不能被模型便利性悄悄替换。
2. **大道至简**：从最简单、可解释、可验证且能完整回答问题的 formulation 开始；复杂度必须由简单 baseline 的真实缺陷来证明。
3. **结构优先**：先检查解析关系、机理、守恒、对称性、单调/凸性、可分性、消元、降维、解耦、coarse-to-fine 与搜索空间压缩，再考虑 solver。
4. **不制造伪机理**：数据驱动问题允许 ML 成为主模型；若已有部分结构，优先 grey-box，而不是为了“机理优先”编造错误方程。
5. **可解释、可验证、可追溯**：关键公式和数字要有来源、sanity check、独立复算或真实泛化证据。
6. **诚实**：真实数据与合成/仿真边界明确；改善、退化和失败都如实保留。
7. **创新少而真**：按 [structural-innovation.md](references/structural-innovation.md) 从问题表示和求解结构中寻找；算法堆砌、冷门模型和改名不是创新，允许 0 个创新点。

权威顺序为：`当届规则/题面 → modeling constitution → structural innovation → production/modeling → model catalog(按需) → 版面/数量等经验建议`。**DAG 是执行器，十阶段是宏观质量门，二者都不是建模哲学。**

默认 `interaction=autonomous`：AI 主动读题、比较 formulation、实现、运行、修错、写作和检查；用户已有决定直接复用。只在缺失关键输入、核心学术判断、最终人工核验或外部行动授权时集中询问。`guided` 是可选教学模式，不要求每阶段回复数字。

[integration-policy.md](references/integration-policy.md) 统一解释导入资料：当届规则优先；旧资料的强制问答、固定图数/字数、尾段强制多代理、旧 AI 声明位置不生效。静态分数不是数学证明或获奖概率，不能覆盖真实错误。

## 启动与恢复

1. 判断备赛/模拟/正式赛/局部任务。复用届次、组别、能力、题面和截止信息。题面未发布只准备环境，保持子问数未知。局部任务只执行对应模块。
2. 读取 `competitions/<comp>/current_rules.md` 并访问官方来源，记录核查日期与来源。CUMCM 2026 是 74h，可用 72h 内部完成；其他赛事不能套同一时长。离线写明未复核。
3. 用 `python <skill>/scripts/workflow.py init --workspace <project> --competition cumcm --year 2026` 建立项目；正式比赛加 `--formal-contest`。已有状态恢复。`state/decision_log.json` 是项目根状态与学术阶段权威；Stage 2 后的 `state/task_dag.json` 是从属任务执行账本，只对任务执行状态权威。二者通过 `workflow.py status/reconcile` 对账。
4. 用 `python <skill>/scripts/doctor.py --competition cumcm --workspace <project>` 检查依赖，只安装所需包。`workflow.py status/next` 查看下一产物。写入型工具始终传项目路径。

## 十阶段路由

| 阶段 | 行为与产物 | 进入时优先读取 |
|---|---|---|
| 0 启动 | 规则、工具、角色、休息与时间预算 | stage_00_kickoff.md、team-workflow.md、schedule.md |
| 1 选题 | 题目包、附件清单、候选比较 | stage_01_problem_selection.md、parsing-tools.md |
| 2 拆解 | 每问目标/变量/约束/产物、来源定位、依赖图与结构扫描 | stage_02_analysis.md、modeling-constitution.md、structural-innovation.md、production/parsing.md |
| 3 选模型 | 先定表示/formulation，再定模型与 solver；必要时做候选/基线/短试跑 | stage_03_model_selection.md、structural-innovation.md、production/modeling.md；**仅 formulation 明确后按需查 model_catalog.md** |
| 4 建基础 | 假设、符号、单位、术语及数据口径 | stage_04_foundation.md、共享表格模板 |
| 5 求解 | 每问可运行实现、结果、日志、解释；按需 baseline/proposed 对照 | stage_05_subproblem_loop.md、production/coding.md、code_starter |
| 6 稳健性 | 有依据的扰动、边界/误差/残差检查；对 adopted innovation 做定向 failure test | stage_06_robustness.md、structural-innovation.md、verification.md |
| 7 评价 | 优点、证据、局限和适用范围 | stage_07_evaluation.md |
| 8 论文 | 编号章节、真实引用、LaTeX/PDF、AI 报告；只写 verified innovation claim | stage_08_writing.md、paper-tools.md、academic-style.md、production/writing.md、production/visualization.md、architecture-diagram.md |
| 9 终审 | 重跑证据、引用、版面、页面图、合规与冻结清单 | stage_09_review.md、production/review.md、当届规则 |

第 8 阶段草稿从第 2 阶段开始积累，正式完成时间不等于写作开始。按依赖并行；上游改变后标记依赖结果过期，重算再更新论文。

## Stage 2 后：DAG 是实际调度中心

Stage 0–2 负责统一读题、选题和问题分解；**Stage 2 完成后，日常执行以 `task_dag.json` 为中心，而十阶段主要作为 macro quality gates。** `task_dag.py init` 默认生成每问 `model → solve → verify → write` 骨架以及 foundation/data/paper 三条共享线，A/B/C 只要依赖满足就并行领取 ready task。

`TQi-model` 必须读取 Stage 2 的 `structure_scan` 和建模宪法；只有某个 innovation opportunity 值得验证时，才用 `task_dag.py replan` 动态插入 baseline/proposed/compare 或 ablation 任务。创新候选失败时保留证据并标记 rejected，不为了论文创新点继续使用错误方案。

## 自动化工具

完整命令见 [toolchain.md](references/toolchain.md)。语义理解和生成由当前 AI 执行，脚本负责确定性解析、状态、检查和渲染，不假称可自动求解任意赛题；不需要特定模型 API 密钥。

- `parse_problem.py`：PDF/DOCX/Markdown/TXT 文本、分问候选、来源定位、CSV/Excel 概况和题型候选；扫描页标记待 OCR。
- `task_dag.py`：Stage 2 后把任务组成 DAG 派给 A/B/C；支持 board、done、replan、invalidate、产物 SHA 和交叉复核。
- `workflow.py`：初始化、恢复、下一步、阶段完成与回退；`reconcile` 在每次 autonomous 会话收尾前只读检查阶段账、DAG、产物漂移和 bookkeeping lag。
- `score_artifact.py`：L1 评分校验、逐问聚合与日志持久化；L2/L3/L4 按风险和时间选用。
- `render_paper.py`：10 个 Markdown 章节→三赛事 LaTeX→PDF，支持 XeLaTeX/pdfLaTeX/Tectonic。
- `render_ai_usage.py`：真实台账导出；按赛事生成声明/报告。
- `pdf_audit.py`：赛事页数、缺字、占位、元数据、图形密度、TeX Overfull/Underfull 与逐页 PNG；视觉复核回执后才可 passed。
- `check_layout.py`：**advisory 版面 lint**，检查图表引用距离、图形密度、图挨图、caption 长度与目标页数等。除显式 `--hard-max-pages` 或乱码外不把经验阈值冒充赛事硬规则。
- `citation_audit.py`：参考文献与正文引用一致性。
- `verify_independence.py`：独立复算的结构性防同源门。
- `claim_registry.py`：headline/innovation claim 的 source、验证器和 SHA provenance。
- `final_gate.py`：汇总 workflow、claims、citation、PDF、合规，输出唯一 `READY/BLOCKED`。
- `prose_lint.py`：保护数字、公式、引用与否定边界的表达 lint。
- `corpus.py`：本地论文导入、去重、QA 与统计。
- `scripts/diagrams/check_overlap.py`：架构图文字重叠/越界提示；规范见 `references/architecture-diagram.md`。

## 三人、AI 和低干预协作

A 管模型，B 管数据求解，C 管论证交付，可按能力调整。Stage 2 后切换为 DAG 派单：任务成图、就绪即认领、完成需交叉复核、上游变化级联失效并可重规划。任务卡包括输入版本、可写范围、输出、验收、时限、负责人和复核人。同一文件单写者，主协调人写根状态；任务执行状态只写 DAG。

创新 benchmark 同样职责分离：典型做法是 A 负责结构/formulation，B 跑公平 baseline/proposed，C 或另一角色复核指标、失败边界和论文证据。不得由同一执行者提出、实现、复核并自行宣布收益。

少数真实人工节点：选题和核心假设、核心结果核验、最终作品。AI 先做成可检查产物再集中交接，不让人手工管理 JSON、命令和例行错误。遇可修复的 high issue 自动修复重跑；block 表示不放行错误产物，不等于停止所有工作。

原始数据只读，动态脚本通过 workspace-relative 路径/CLI/config 定位数据；日志可记录解析后的绝对路径用于诊断，但**不得把个人机器绝对路径写死进可复现代码或交付物**。合成/仿真数据必须明确标注。用 run_id、数据/代码摘要、配置及验证证据追溯。

## 交接

将结果、假设变化、放弃方案及理由、未决项、下一产物和预计耗时写入主状态。恢复先核对状态和产物存在性。**每次 autonomous 工作会话结束前必须运行 `workflow.py reconcile --workspace <project>`；出现 bookkeeping-lag、artifact-drift 或 DAG inconsistency 时先修账/回退/重验，不带着未对账状态结束。**
