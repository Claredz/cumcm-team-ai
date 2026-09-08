# CUMCM Team AI · v2

面向 CUMCM 国赛、MCM/ICM 与电工杯的数学建模全流程 skill。核心定位不是“算法目录”，而是：**建模原则优先 + Stage 2 后三人 DAG 并行 + 可复现/可审计证据 + 论文与最终交付**。

本版整合 [LEEHAHAHAHA/math-modeling-skill](https://github.com/LEEHAHAHAHA/math-modeling-skill) 的竞赛建模/写作经验与 [handsomeZR-netizen/mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill) 的阶段、反馈和赛事资产，并在此基础上加入结构创新协议、状态/DAG、provenance、独立复算与 CI。来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 先看建模原则

[modeling-constitution.md](references/modeling-constitution.md) 是最高层方法论：忠于题目、大道至简、结构优先、可解释、真实数据、诚实证据；复杂度必须由简单 baseline 的实际缺陷证明。创新按 [structural-innovation.md](references/structural-innovation.md) 从降维、消元、解耦、coarse-to-fine、剪枝、grey-box 等结构中寻找。

权威顺序：

`当届规则/题面 → modeling constitution → structural innovation → production/modeling → model catalog(按需) → 图数/页数/配色等经验建议`

`model_catalog.md` 因此是 formulation 明确后的工具书，不是“预测→LSTM / 优化→GA”的关键词路由器。

## 能力与实际文件

| 能力 | 实现 |
|---|---|
| 建模宪法与结构创新 | [modeling-constitution.md](references/modeling-constitution.md)、[structural-innovation.md](references/structural-innovation.md) |
| 题面提取、分问与题型候选 | [parse_problem.py](scripts/parse_problem.py)：PDF/DOCX/MD/TXT、页行定位、CSV/XLSX 概况；扫描页提示 OCR |
| 三人并行执行 | [task_dag.py](scripts/task_dag.py)：Stage 2 后 model→solve→verify→write、ready board、交叉复核、replan、stale cascade |
| 十阶段宏观质量门 | references/stage_00…stage_09；[workflow.py](scripts/workflow.py) 初始化、恢复、产物摘要、推进/回退/reconcile |
| 候选模型与代码起步 | [production/modeling.md](references/production/modeling.md) 优先；必要时查 [model_catalog.md](references/model_catalog.md)；五类 [code_starter](templates/shared/code_starter) |
| 结果与创新 provenance | [claim_registry.py](scripts/claim_registry.py)、[verify_independence.py](scripts/verify_independence.py)、SHA 证据漂移检查 |
| 评分与四层反馈 | [score_artifact.py](scripts/score_artifact.py)、rubrics、L1/L2/L3/L4，按风险与时间使用 |
| 论文与 LaTeX | [生产指南](references/production)、三赛事装配模板、[render_paper.py](scripts/render_paper.py)，支持 Pandoc + XeLaTeX/pdfLaTeX/Tectonic |
| 架构图与流程图 | [architecture-diagram.md](references/architecture-diagram.md)、[architecture.tex](templates/diagrams/architecture.tex)、[flow_snake.tex](templates/diagrams/flow_snake.tex)、[check_overlap.py](scripts/diagrams/check_overlap.py) |
| PDF 与版面检查 | [pdf_audit.py](scripts/pdf_audit.py) 负责赛事/损坏/视觉 gate；[check_layout.py](scripts/check_layout.py) 负责 advisory 图文关系与版面 lint |
| 引用一致性 | [citation_audit.py](scripts/citation_audit.py) |
| AI 使用披露 | [render_ai_usage.py](scripts/render_ai_usage.py)，按赛事生成声明/报告 |
| 往届论文资料与统计 | [data/papers](data/papers)、本地导入/去重/QA/分组统计 |
| 跨平台运行 | GitHub Actions 同时回归 `ubuntu-latest` / `windows-latest`；[Windows](references/setup-windows.md) 与 [Linux/WSL2](references/setup-linux-wsl.md) 独立配置指南 |
| 自动化测试 | tests/ + GitHub Actions；含夜间学习空间事故回归、结构创新和质量门测试 |

分问和题型脚本输出只是候选。AI 继续核对原题、图、公式和隐含约束；脚本不宣称能独立理解或求解任意题目。

## 平台支持

正式支持目标：

- Windows 10/11 + PowerShell；
- Linux；
- Windows + WSL2。

核心 Python workflow 不要求 Bash。Windows 和 Ubuntu 都由 CI 跑同一套 unittest、compileall 和三赛事 doctor 核心检查。Pandoc、TeX、字体等大型外部工具仍由每台比赛机本地 `doctor.py` 预检。

详细配置：

- [Windows 10/11 原生 PowerShell](references/setup-windows.md)
- [Linux / WSL2](references/setup-linux-wsl.md)

## 项目级安装

Linux / WSL2：

```bash
mkdir -p .agents/skills
git clone https://github.com/Claredz/cumcm-team-ai.git .agents/skills/cumcm-team-ai
python -m pip install -r .agents/skills/cumcm-team-ai/requirements.txt
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force .agents\skills | Out-Null
git clone https://github.com/Claredz/cumcm-team-ai.git .agents\skills\cumcm-team-ai
python -m pip install -r .agents\skills\cumcm-team-ai\requirements.txt
```

推荐提示：

```text
使用 $cumcm-team-ai。按 autonomous 模式推进。
先忠于题目做 structure scan 和最简 baseline，Stage 2 后生成 DAG 给三人并行。
只有简单模型的真实缺陷被证据证明后才升级复杂度；最终结果与论文数字必须通过复算和 provenance gate。
```

## 最短运行路径

Python 3.10+。核心 CLI 参数在 Windows/Linux 相同，路径由 `pathlib` 处理。以下从项目根运行：

```text
python .agents/skills/cumcm-team-ai/scripts/workflow.py init --workspace . --competition cumcm --year 2026
python .agents/skills/cumcm-team-ai/scripts/doctor.py --competition cumcm --workspace .
python .agents/skills/cumcm-team-ai/scripts/parse_problem.py problem/problem.pdf --attachments data/raw/data.xlsx --output state/problem-package.json
python .agents/skills/cumcm-team-ai/scripts/workflow.py next --workspace .
```

求解脚本应通过 `--workspace` / config / manifest 使用项目相对路径定位数据；解析后的绝对路径可以写日志用于诊断，但不要把个人机器路径硬编码进代码或支撑材料。

正式论文转换需要 Pandoc 与 TeX/Tectonic。详细命令见 [toolchain.md](references/toolchain.md)、[paper-tools.md](references/paper-tools.md)、[parsing-tools.md](references/parsing-tools.md)。

## DAG 与阶段的关系

Stage 0–2 统一读题、选题、拆解和结构扫描。Stage 2 完成后，`task_dag.json` 是实际执行看板，A/B/C 在依赖满足时并行领取任务；十阶段只做项目级 macro gate。上游改变后，下游 task 级联 stale，重新求解与验证后再更新论文。

主状态是 `state/decision_log.json`，DAG 是从属执行账本；二者通过 `workflow.py status/reconcile` 对账，不能各自独立解释“项目是否完成”。

## 论文质量门

`pdf_audit.py` 负责官方页数边界、缺字/占位、Overfull/Underfull、元数据和真实视觉复核；`check_layout.py` 只对图表引用距离、图挨图、caption 长度、目标页数和图形密度给 `review/hint`，不把 21–30 页、100–150 字 caption 或固定图数伪装成赛事规则。引用、关键数字和 innovation claims 分别由 citation/claim/final gate 检查。

## 验证与开发

跨平台核心回归命令相同：

```text
python -m unittest discover -s tests -v
python -m compileall -q scripts templates/shared/code_starter
python scripts/doctor.py --competition cumcm --skip-tools
python scripts/doctor.py --competition mcm --skip-tools
python scripts/doctor.py --competition diangong --skip-tools
```

CI 在 Windows 与 Ubuntu 上都运行以上检查。继承的经验建议统一由 [integration-policy.md](references/integration-policy.md) 适配；不强制每问图数、公式数、最低正文页数或每阶段人工确认。数学正确性始终以实际推导、实验和验证为准。
