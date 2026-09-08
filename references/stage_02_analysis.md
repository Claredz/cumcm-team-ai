---
stage: 2
name: analysis
duration_h: 2-3
inputs:
  - "stage.1.selected"
  - "problem_pdf"
  - "attachment_data_paths"
outputs:
  - "stage.2.{decomposition, key_variables, key_constraints, objective_per_subproblem, data_schema, subproblem_dependency, structure_scan, innovation_opportunities}"
loads_reference:
  - "references/rubrics.md§Stage_2"
  - "references/structural-innovation.md"
feedback: ["L1"]
next: stage_03_model_selection
---

# Stage 2 — 问题深度解析、结构扫描与分解

> v2 适配：本页为导入参考。执行前以根 SKILL.md 和 references/integration-policy.md 为准：默认自主推进，普通修错不等待确认；固定图数/字数只作建议；赛事规则与 AI 披露以当前比赛包为准。旧问答示例仅用于 guided 模式。

**时长**: 2-3h | **反馈层**: L1

## 目标

把题目从自然语言转化为数学语言骨架：识别决策变量、目标函数、约束、数据接口和子问题关系；同时在选算法前执行一次**问题结构扫描**，寻找可验证的降维、消元、分解、粗到细和搜索空间压缩机会。这一步决定后续 Stage 3/5/6/8 的天花板。

结构扫描只生成 innovation hypothesis，不要求每题必须创新。找不到有依据的结构机会时明确记录 `none`，禁止为了创新感强行制造复杂模型。

## 输入

- Stage 1 输出：选定题号 + 子问题清单 + 数据路径
- 题目原文（再读一次）
- 附件数据（用 pandas/Read 扫 schema）
- `references/structural-innovation.md`

## 产出

- 子问题分解树（全部 Qi 的输入/输出/约束/目标）
- 关键变量清单（决策/状态/参数）
- 子问题关联图，区分**模型结构依赖**和**已验证结果依赖**
- 目标函数雏形
- 数据 schema 与变量映射
- 每个 Qi 的 `structure_scan`
- 0 个或多个 `innovation_opportunities`；它们仅是候选，不是论文创新点

## 操作流程

### Step 1：题目精读（30 min）

精读三遍，每遍不同任务：

1. 抓动词：题目要求求最优、预测、评价、解释还是仿真？
2. 抓约束：哪些条件不能违反，哪些只是背景描述？
3. 抓数据接口：哪些参数题目给，哪些来自附件，哪些必须估计或假设？

### Step 2：子问题正式分解（45 min）

对每个 Qi 填卡片：

```text
Q1 卡片
├── 自然语言描述
├── 输入
│   ├── 题目给定参数
│   ├── 附件字段
│   └── 上游结果
├── 输出（最终决策/估计量，含单位）
├── 约束
├── 目标
├── 问题类型
└── 难度估计
```

必须区分两种依赖：

- `model_depends_on`：下游模型定义/结构依赖上游模型、假设或符号合同，只要求上游模型合同批准。
- `result_depends_on`：下游正式求解需要上游数值结果、估计参数、预测值或标签，必须等待上游 `verify` 完成。

只有题面、数学接口或业务机制支持时才建立依赖；没有合理依赖时写空数组并保留理由。

### Step 3：关键变量统一编号（25 min）

建立全局变量表：

| 符号 | 含义 | 单位 | 类型 | 出现于 |
|---|---|---|---|---|
| `x_i` | 第 i 个决策量 | 件 | 决策变量 | Q1,Q2 |
| `p_i` | 单价 | 元/件 | 参数 | Q1,Q3 |

只收录实际出现在目标、约束、数据映射或验证中的变量。无用途变量删除。

### Step 4：数据 schema 扫描（25 min）

至少检查 shape、dtype、描述统计、缺失、异常口径和字段到模型变量的映射。扫描结果必须来自实际附件，不预填。

### Step 5：问题结构扫描（30–45 min）

在查看算法目录之前，对每个 Qi 逐项检查 `references/structural-innovation.md`：

```json
{
  "Q1": {
    "symmetry_or_invariance": [],
    "eliminable_intermediates": [],
    "separable_components": [],
    "monotonicity_or_convexity": [],
    "scale_separation": [],
    "dimensionless_or_relative_form": [],
    "coarse_to_fine_opportunity": [],
    "search_space_reduction": [],
    "mechanism_data_boundary": [],
    "key_approximation_candidates": []
  }
}
```

每一项必须是：

- 有题面/数学/数据依据的具体机会；或
- `none: <为什么没有>`。

重点追问：

- 能否减少自由度、消去难求中间量或改用相对/无量纲形式？
- 是否有可分性、树/图结构、单调性、凸性、稀疏性、守恒量等可利用？
- 是否能先用便宜近似定位区域，再精细求解？
- 是否能剪枝、分块、松弛、局部化或多精度离散？
- 已知机理应承担哪些部分，数据驱动只需补哪些未知项？
- 是否存在解析解、上下界或 toy case 可作为数值基线？

### Step 6：形成 innovation opportunities（15 min）

只把有明确“观察 → 改变 → 预期收益 → 风险 → 证据需求”的结构机会写入候选：

```json
{
  "id": "I1",
  "subproblem": "Q3",
  "type": "coarse_to_fine",
  "observation": "...",
  "proposed_change": "...",
  "expected_benefit": "...",
  "risk": "...",
  "evidence_needed": "...",
  "status": "candidate"
}
```

没有合格候选时 `innovation_opportunities=[]`。不得为了数量填充。

### Step 7：子问题关系图与目标函数雏形（25 min）

用 Mermaid/ASCII 表示依赖并标接口，然后为每个 Qi 写符号化目标/约束骨架。若使用上游结果或 warm start，注明依赖类型与依据。

### Step 8：输出移交

写入 `decision_log.stages.2`：

```json
{
  "decomposition": [],
  "key_variables": [],
  "key_constraints": [],
  "objective_per_subproblem": {},
  "data_schema": {},
  "subproblem_dependency": {
    "Q1": {"model_depends_on": [], "result_depends_on": []},
    "Q2": {"model_depends_on": [], "result_depends_on": ["Q1"]}
  },
  "structure_scan": {},
  "innovation_opportunities": []
}
```

旧版 `"Q2": ["Q1"]` 仍兼容，但新项目必须显式区分两类依赖。

## L1 Rubric

| 维度 | 满分行为 |
|---|---|
| 子问题分解 | 每 Qi 输入/输出/约束/目标完整 |
| 关键变量 | 覆盖实际模型所需项，无占位变量 |
| 数学化 | 每 Qi 有数学对象、目标或关系骨架 |
| 数据契合 | schema 已扫并与变量映射 |
| 结构与依赖 | 依赖类型明确；结构扫描有依据或诚实记录 none |

## 常见坑

- 读一遍题就开始选算法；
- 为了“串起来”强行依赖上游；
- 看到“优化/预测”关键词就直接跳到 GA/LSTM；
- 把“改进算法名”写成结构机会；
- 强制每问找创新点；
- 结构扫描只写术语，不说明它如何改变 formulation 或 solver。

## 退出条件

1. 全部子问题卡片完整；
2. 全局变量表与数据 schema 完成；
3. 模型依赖/结果依赖明确；
4. 每个 Qi 完成 structure scan；
5. innovation opportunities 只包含有依据、可证伪的候选，允许为空；
6. L1 rubric 达到工作流阈值。

拆解后启用 DAG 派单：`task_dag.py init --workspace <project>`。默认 `TQi-model` 必须读取本阶段的 `structure_scan` 和 innovation opportunities；只有某个候选值得验证时，才通过 `task_dag.py replan` 动态插入 baseline/proposed/compare 任务，不新增固定“创新阶段”。
