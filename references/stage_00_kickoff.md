---
stage: 0
name: kickoff
duration_h: 1
inputs:
  - "user_inputs.{competition, problem_id, team_size, deadline, pdf_path}"
outputs:
  - "stage.0.{team_roles, tools_ready, problem_scan, time_budget_h, collab_protocol, checklist_completed}"
  - "root.{competition, task_type}"
loads_reference:
  - "competitions/<comp>/current_rules.md"
  - "competitions/<comp>/topic_specs.json"
  - "competitions/<comp>/README.md"
  - "references/setup-windows.md | references/setup-linux-wsl.md when environment repair is needed"
loads_template:
  - "templates/shared/decision_log.json"
  - "templates/shared/requirements.txt"
feedback: ["L1"]
next: "stage_01_problem_selection | wait_for_prompt"
---

# Stage 0 — 团队启动与资料预扫

> 执行前以根 `SKILL.md`、`modeling-constitution.md` 和 `integration-policy.md` 为准。默认自主推进；赛事规则与 AI 披露以当前比赛包为准。Windows PowerShell、Linux 与 WSL2 都是一等运行环境，不要求队员为了本 skill 临时学习另一套 shell。

**时长**: 1h | **反馈层**: L1 | **触发**: skill 首次启动 / 用户说“开始建模”

## 目标

在题目正式公布前或公布后立即，把队伍状态调到“可直接执行”：规则已核、角色明确、每台比赛机核心工具可用、协作路径一致。避免后续阶段因平台、路径、环境或职责问题返工。

## 输入与产出

输入：队员数、截止时间、模式偏好；题目已发布时读取题面和附件。

产出：

- `state/decision_log.json` 初始化；
- 角色分工表；
- 每台机器工具就绪记录；
- 初步问题域识别；
- 真实 deadline 驱动的时间预算。

## Step 1：元信息收集

先合并当前消息与已有 state，只询问缺失字段：竞赛、题号、队员与擅长、截止时间、题面/附件位置。禁止让用户手动编辑 `decision_log.json`。

先读 `competitions/<comp>/current_rules.md`，再复核其中的官方来源；仓库经验值不能覆盖当届通知。题面未公布时，子问数和 task type 保持未知，不根据历史题猜测。

## Step 2：角色分工

确保建模、求解、写作/交付三类职责都有真实主责和互备。Stage 2 后由 DAG 动态派单，不把 A/B/C 锁死成“每人只做一问”。

反模式：人人都负责一切，实际无人对 artifact 负责。每个文件保持单写者，每个关键 task 的 reviewer 与 owner 分离。

## Step 3：每台机器环境预检

核心要求：**优先调用跨平台 Python CLI，而不是手工复制 Bash 命令。**

所有平台都先运行：

```text
python --version
python <skill>/scripts/doctor.py --competition <comp> --workspace <project>
```

`doctor.py` 会显示当前平台标签，并检查 Python、skill 包结构、竞赛包、状态，以及按需检查 Pandoc、TeX 和建模依赖。Windows/Linux/WSL 的核心 workflow 参数一致。

如果需要完整建模栈：

```text
python -m pip install -r <skill>/templates/shared/requirements.txt
python <skill>/scripts/doctor.py --competition <comp> --workspace <project> --require-modeling
```

正式论文环境还应确认目标赛事的 renderer；不要仅以 `--skip-tools` 结果代表比赛机可交付。CUMCM/电工杯通常需要 XeLaTeX + `ctexart.cls`，MCM/ICM 通常需要 pdfLaTeX；Pandoc 由 doctor 检查。

若 doctor 报平台/安装问题：

- Windows 原生 PowerShell → `references/setup-windows.md`；
- Linux / WSL2 → `references/setup-linux-wsl.md`。

不要求 Windows 队员安装 Git Bash；不要求已经熟悉 Windows 的队员临时迁移 WSL。三台机器允许不同 OS，只要 Python CLI、项目相对路径和 artifact 协议一致。

目录与状态初始化统一由：

```text
python <skill>/scripts/workflow.py init --workspace <project> --competition <comp> --year <year>
```

完成，不再通过 `mkdir -p` / `cp` 作为权威初始化路径。

## Step 4：跨平台路径约定

DAG、manifest、claim source 和论文引用只记录项目相对逻辑路径，例如：

```text
data/raw/附件1.xlsx
runs/Q1/final/result.json
paper_workspace/main.tex
```

运行日志可记录解析后的 `C:\...`、`/home/...` 或 `/mnt/c/...` 绝对路径用于诊断，但最终代码和共享状态不得依赖某一位队员机器的绝对路径。Python 使用 `pathlib.Path`，不要手工拼接 `/` 或 `\\`。

WSL 队员优先把高频 Python/Git/TeX 工作区放在 WSL 文件系统；Windows 队员保持原生 PowerShell 环境即可。

## Step 5：题目预扫

题目发布后，用当前 harness 可用的文件工具完整核对题面、图、公式与附件，再做快速识别。至少记录：

```json
{
  "problem_id": "<official year-letter>",
  "domain_keywords": [],
  "data_attachments": [],
  "subproblem_count": null,
  "primary_problem_type": "<evidence-based candidate>",
  "secondary_types": [],
  "estimated_difficulty": "<with rationale>",
  "data_size_signal": "<actual scan>"
}
```

脚本输出只是候选，不表示语义理解已完成。

## Step 6：时间预算与协作约定

从真实 deadline 倒推。内部可设置提前完成缓冲，但不能把内部 72h/96h 预算冒充官方赛程。题面未公布时不猜每问耗时；公布后根据实际依赖、数据清洗、求解成本、论文和提交要求再分配。

写入协作约定：

- 命名、单位、数据 schema；
- Git/共享产物边界；
- DAG task 单写者与 reviewer；
- 每次同步包含阻断项、交接 artifact、下一步；
- 三台机器的项目逻辑路径一致，平台专属绝对路径不进入共享证据。

## L1 Rubric

参考 `rubrics.md` Stage 0。重点不是“装了多少软件”，而是规则核对、角色清晰、平台可运行、时间预算和协作协议是否足以支撑正式比赛。

## 退出条件

1. `decision_log.stages.0.checklist_completed == true`；
2. 团队角色明确；
3. 每台将参与核心任务的机器通过对应的基础 doctor，正式交付机验证 renderer；
4. 跨平台路径约定写清；
5. 题面已发布时完成预扫；未发布则停在 Stage 0 等待，不伪造题目结构；
6. L1 达到当前 workflow 阈值。

题面可读后进入 Stage 1；题面不可读则保持当前状态，恢复时从题面预扫继续，不重复环境和角色准备。
