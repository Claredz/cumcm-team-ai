---
name: cumcm-team-ai
description: 数学建模全流程 skill，覆盖 CUMCM 国赛、MCM/ICM 与电工杯的题面解析、模型选型、代码求解、稳健性、论文写作与编译、PDF 审查、十阶段状态评分和三人 AI 协作。用于备赛、正式参赛及建模论文，不用于普通数据分析。默认自动推进，核心学术判断与最终成果保留队员核验。
---

# 数学建模全流程 · cumcm-team-ai v2

默认 interaction=autonomous：AI 主动读题、比较方案、实现、运行、修错、写作和检查；用户已有决定直接复用。只在缺失关键输入、核心学术判断、最终人工核验或外部行动授权时集中询问。guided 是可选教学模式，不要求每阶段回复数字。

本入口及 [integration-policy.md](references/integration-policy.md) 统一解释导入资料：当届规则优先；旧资料的强制问答、固定图数/字数、尾段强制多代理、旧 AI 声明位置不生效。静态分数不是数学证明或获奖概率，不能覆盖真实错误。

## 启动与恢复

1. 判断备赛/模拟/正式赛/局部任务。复用届次、组别、能力、题面和截止信息。题面未发布只准备环境，保持子问数未知。局部任务只执行对应模块。
2. 读取 competitions/<comp>/current_rules.md 并访问官方来源，记录核查日期与来源。CUMCM 2026 是 74h，可用 72h 内部完成；其他赛事不能套同一时长。离线写明未复核。
3. 用 `python <skill>/scripts/workflow.py init --workspace <project> --competition cumcm --year 2026` 建立项目；正式比赛加 `--formal-contest`，模拟/准备不加。已有状态恢复。唯一主状态为 state/decision_log.json，包括十阶段、评分、团队、交接、AI 台账。旧 team-state.json 只作迁移输入。
4. 用 `python <skill>/scripts/doctor.py --competition cumcm --workspace <project>` 检查依赖，只安装所需包。workflow.py status/next 查看下一产物。写入型工具始终传项目路径。

## 十阶段路由

| 阶段 | 行为与产物 | 进入时读 references/ 下的文件 |
|---|---|---|
| 0 启动 | 规则、工具、角色、休息与时间预算 | stage_00_kickoff.md、team-workflow.md、schedule.md |
| 1 选题 | 题目包、附件清单、候选比较 | stage_01_problem_selection.md、parsing-tools.md |
| 2 拆解 | 每问目标/变量/约束/产物、来源定位和依赖图 | stage_02_analysis.md、production/parsing.md |
| 3 选模型 | 候选、基线、短试跑、验证计划及取舍 | stage_03_model_selection.md、model_catalog.md、production/modeling.md |
| 4 建基础 | 假设、符号、单位、术语及数据口径 | stage_04_foundation.md、共享表格模板 |
| 5 求解 | 每问可运行实现、结果、日志、解释 | stage_05_subproblem_loop.md、production/coding.md；templates/shared/code_starter/ |
| 6 稳健性 | 有依据的扰动、边界/误差/残差检查 | stage_06_robustness.md、verification.md |
| 7 评价 | 优点、证据、局限和适用范围 | stage_07_evaluation.md |
| 8 论文 | 编号章节、真实引用、LaTeX/PDF、AI 报告 | stage_08_writing.md、paper-tools.md、academic-style.md、production/writing.md、production/visualization.md |
| 9 终审 | 重跑证据、页面图、合规检查、冻结清单 | stage_09_review.md、production/review.md、当届规则 |

第 8 阶段草稿从第 2 阶段开始积累，正式完成时间不等于写作开始。按依赖并行；上游改变后标记依赖结果过期，重算再更新论文。

## 自动化工具

完整命令见 [toolchain.md](references/toolchain.md)。语义理解和生成由当前 AI 执行，脚本负责确定性解析、状态、检查和渲染，不假称可自动求解任意赛题；不需要特定模型 API 密钥。

- parse_problem.py：PDF/DOCX/Markdown/TXT 文本、分问候选、来源定位、CSV/Excel 概况和题型候选；扫描页标记待 OCR。AI 核对公式、分问和隐含约束后完善题目包。
- workflow.py：初始化、恢复、下一步、阶段完成与回退。阶段完成需实际文件摘要和检查记录，正式赛核心节点需真实人工复核，可集中进行。
- score_artifact.py：L1 评分校验、加权、逐问聚合与日志持久化。L2 定向回检、L3 多视角、L4 经验校准见 feedback_layer*.md，按风险和时间选用。
- render_paper.py：10 个 Markdown 章节→三赛事 LaTeX→PDF，支持 XeLaTeX/pdfLaTeX 及 Tectonic。--no-compile 只产生结构稿。
- render_ai_usage.py：真实台账导出；国赛参考文献前声明及详情 PDF，美赛 AI 报告，电工杯内部台账（提交位置按当届规定）。
- pdf_audit.py：按赛事区分摘要/正文/附录/AI 报告计页，检查缺字、溢出、元数据和图形密度，渲染逐页 PNG；自动检查配合视觉核验。
- prose_lint.py：中英表达建议及改写前后数字、公式、引用对照；不自动改原文，不宣称检测 AI 率。
- corpus.py：本地论文导入、SHA256 去重、提取 QA、索引、按年/题型统计。data/papers/ 包含来源数据集和上游统计来源；全文不默认公开分发。

## 三人、AI 和低干预协作

A 管模型，B 管数据求解，C 管论证交付，可按能力调整。任务卡包括输入版本、可写范围、输出、验收、时限、负责人和复核人。默认建议 3 条产出线加可选只读检查线。同一文件单写者，主协调人写状态。实际子代理/外部任务遵守用户与环境授权，读取 skill 本身不创建新任务。

少数真实人工节点：选题和核心假设、核心结果核验、最终作品。AI 先做成可检查产物再集中交接，不让人手工管理 JSON、命令和例行错误。遇可修复的 high issue 自动修复重跑；block 表示不放行错误产物，不等于停止所有工作。

原始数据只读，模拟数据明确标注。用 run_id、数据/代码摘要、配置及验证证据追溯。失败如实记录，未运行代码不是结果。夜间仅有限时批处理，保留三晚连续睡眠，不让无人值守 AI 无限扩写主稿。

学术语言改进保留事实、公式、单位、置信区间、否定、限制和引用。humanizer 的生活化、编造经历和检测器分数目标不用于论文。实际 AI 使用按当届要求披露。

## 交接

将结果、假设变化、放弃方案及理由、未决项、下一产物和预计耗时写入主状态。上下文保留摘要和路径，按需读文件；恢复先核对状态和产物存在性。
