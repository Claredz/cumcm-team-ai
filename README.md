# CUMCM Team AI · v2

覆盖读题、建模、求解、稳健性、论文写作、LaTeX 编译、PDF 审查与交付的全流程 skill。支持 **CUMCM 国赛、MCM/ICM、电工杯**，默认 AI 自主推进，三人保留核心学术判断与成果核验。

本版大量整合 [LEEHAHAHAHA/math-modeling-skill](https://github.com/LEEHAHAHAHA/math-modeling-skill) 与 [handsomeZR-netizen/mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill)，保留来源许可并修正规则与交互冲突。完整来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 能力与实际文件

| 能力 | 实现 |
|---|---|
| 题面自动提取、分问与题型候选 | [parse_problem.py](scripts/parse_problem.py)：PDF/DOCX/MD/TXT，页行定位，CSV/XLSX 概况；扫描页提示 OCR |
| 模型目录与代码起步 | [model_catalog.md](references/model_catalog.md)；[五类代码模板](templates/shared/code_starter)涵盖预测、分类、评价、优化、仿真 |
| 完整十阶段流程 | references/stage_00…stage_09；[workflow.py](scripts/workflow.py) 初始化、恢复、产物摘要、阶段推进与回退 |
| 评分与四层反馈 | [score_artifact.py](scripts/score_artifact.py)、rubrics、L1 Critic/L2 回检/L3 Panel/L4 校准、逐问聚合 |
| 全套论文写作与 LaTeX | [生产指南](references/production)、三赛事装配模板、[render_paper.py](scripts/render_paper.py)，支持 Pandoc + XeLaTeX/pdfLaTeX/Tectonic |
| 自动 PDF 检查与渲染 | [pdf_audit.py](scripts/pdf_audit.py)：比赛计页、溢出/缺字/占位、元数据、密度提示、逐页 PNG |
| 往届论文资料与统计 | [data/papers](data/papers)：35 条官方论文元数据；继承上游 59 份可提取样本的观察统计；本地导入、去重、QA、分组统计 |
| 中文/英文表达改进 | [academic-style.md](references/academic-style.md)、两种 humanizer 参考、write-good 可选集成、[prose_lint.py](scripts/prose_lint.py) |
| AI 使用披露 | [render_ai_usage.py](scripts/render_ai_usage.py)，国赛 2026 声明与详情 PDF、美赛 AI 报告、电工杯内部台账 |
| 三人协作与休息 | 任务卡、文件单写者、结果版本、交叉核验、三晚连续睡眠与截止缓冲 |
| 自动化测试 | tests/ 覆盖评分、状态、代码模板、解析、语料、PDF、语言保护、渲染异常；GitHub Actions 自动执行 |

分问与题型脚本输出是候选，不是语义理解已完成。AI 继续核对原题、图、公式和隐含约束；脚本不宣称能独立求解任意题目。

## 项目级安装

在需要使用 skill 的项目根目录执行：

```bash
mkdir -p .agents/skills
git clone https://github.com/Claredz/cumcm-team-ai.git .agents/skills/cumcm-team-ai
```

不需要全局安装。使用：

```text
使用 $cumcm-team-ai。我们参加 2026 国赛，按 autonomous 模式推进。
先读题、检查附件、提出并试跑模型，然后完成求解、验证和论文。
例行选择你自行决定并记录，关键学术判断和最终结果集中交给我们复核。
```

也可指定 guided 教学模式，或只执行某个局部任务。现有团队分工和工具选择优先。

## 工具安装与使用

Python 3.10+。按需安装核心依赖：

```bash
python -m pip install -r .agents/skills/cumcm-team-ai/requirements.txt
```

正式论文转换需要 Pandoc，编译使用已有 TeX 引擎或 Tectonic；图表、TeX 资源、OCR 的依赖按实际环境检查。核心代理工作流不依赖特定厂商 API 密钥，AI 会替用户执行本地命令，不要求人手工管理 JSON。

以 skill 根目录为当前目录，可运行：

```bash
python scripts/workflow.py init --workspace /path/to/project --competition cumcm --year 2026
python scripts/doctor.py --competition cumcm --workspace /path/to/project
python scripts/parse_problem.py /path/to/project/problem.pdf --attachments /path/to/project/data.xlsx --output /path/to/project/state/problem-package.json
python scripts/workflow.py next --workspace /path/to/project
```

详细命令见 [工具链](references/toolchain.md)、[论文编译](references/paper-tools.md)、[题面解析](references/parsing-tools.md)。正式比赛初始化加 `--formal-contest`，关键节点只记录真实发生的人工复核，不自动伪造签字。

## 自主推进如何减少人工操作

AI 自动处理候选比较、已有模型实现、代码修错、有限实验、章节拼接、语言润色、图表和检查；问题出现时先修复并重跑。少数核心节点集中交接，避免每阶段反复编号问答。评分的 block 阻止错误产物放行，不表示所有并行任务都停下来。

主状态是 state/decision_log.json；旧 team-state.json 可迁移，不同时维护两个主日志。阶段产物保存 SHA256，改变上游后要求回退重验。每个文件有一个写入者，三人的 AI 任务按依赖拆分，C 从早期就维护论文草稿。

这是一套由 AI 代理执行的工作流，不是脱离任何模型服务的全自动解题程序。数学正确性以实际验证为依据，评分与多个 AI 的一致意见不能替代证明或实验。

## 规则和语料范围

国赛 2026 为 74h，按 72h 内部完成可留下提交缓冲；MCM/ICM 2027 为 99h，截止从当届官方时间计算。国赛声明在参考文献前，MD5 与文件上传是不同截止。详情见各赛事 current_rules.md，赛前与提交前重新核查，赛区/校内要求另列。

论文资料包含官方来源元数据和上游观察统计，未批量再分发论文全文。35 条新索引不等于上游统计的 59 份样本；后者未在本次独立复现。自有或获授权 PDF 可本地导入，保留使用依据、提取 QA 与每组样本量。

语言模块改善表达质量、保护数字/公式/引用和结论边界，不承诺 AI 检测分数，不编造个人经历或省略实际 AI 使用披露。

## 验证与开发

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts templates/shared/code_starter
python scripts/doctor.py --competition cumcm --skip-tools
python scripts/doctor.py --competition mcm --skip-tools
python scripts/doctor.py --competition diangong --skip-tools
```

没有 XeLaTeX 的环境可设置 CUMCM_TEST_TEX_ENGINE 为 Tectonic 路径，执行实际编译及摘要/正文超页拒绝测试。未提供可用编译器时这三项会明确 skip。tests/e2e_render.py 生成标明“合成测试”的回归样稿供三赛事真实编译，不是往届论文或参赛答案。

继承的原始经验建议已由 [integration-policy.md](references/integration-policy.md) 统一适配；不强制每问图数、最低论文页数或每次评分后的人工确认。贡献者请参阅 [AGENTS.md](AGENTS.md)。
