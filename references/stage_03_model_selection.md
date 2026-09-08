---
stage: 3
name: model_selection
duration_h: 2-3
inputs:
  - "stage.2.{decomposition, objective_per_subproblem, data_schema, structure_scan, innovation_opportunities}"
outputs:
  - "stage.3.{candidate_formulations, candidate_models, selected_per_subproblem, rejection_log, toy_demos_passed, innovation_decisions, red_team, model_family_consistency}"
loads_reference:
  - "references/modeling-constitution.md"
  - "references/structural-innovation.md"
  - "references/production/modeling.md"
  - "references/model_catalog.md (on demand after formulation)"
  - "references/rubrics.md§Stage_3"
  - "competitions/<comp>/winning_patterns.md§4"
loads_template: ["templates/shared/code_starter/<problem_type>.py"]
feedback: ["L1", "counterfactual_exploration_in_championship"]
next: stage_04_foundation
---

# Stage 3 — 从问题结构到 formulation，再到模型与求解器

**时长**: 2-3h | **反馈层**: L1 + 反事实探索

## 目标

为每个子问题先确定问题表示与 mathematical formulation，再选择模型族和 solver。必须消费 Stage 2 的 `structure_scan`，并遵守 `modeling-constitution.md`；不能从题型关键词直接跳到算法目录。

默认顺序：

`problem contract → structure → simplest formulation → baseline → diagnose → approximation/decomposition → model family → solver/algorithm`

复杂模型只有在简单 baseline 的具体缺陷被证据量化后才升级。创新优先发生在问题表示、结构利用和求解策略层；标准模型若最适合，就使用标准名称。

## 操作流程

### Step 0：锁定题目契约和 structure scan

逐项确认输出、单位、题面公式/约束和 Stage 2 结构机会。每个 innovation opportunity 做 `adopt for testing / reject`，记录依据、风险和需要的 baseline/guard。没有结构机会是合法结果。

### Step 1：构造最简单可行 formulation

在打开算法目录前依次检查：

1. 是否有解析关系、守恒量、上下界、单调性、凸性或对称性？
2. 是否有中间量可以消去，或通过无量纲化/相对量/重参数化简化？
3. 是否可以分块、解耦、松弛或按图/树结构局部计算？
4. 是否能 coarse-to-fine、剪枝、局部化或 warm start 缩小求解域？
5. 已知机理与数据驱动边界在哪里？是否适合 grey-box？

形成 `candidate_formulations`，而不是算法名单。

### Step 2：先建立 baseline，再证明是否需要升级

baseline 应是公平、简单、可复现且能回答相同任务的方案。记录其误差、残差、可行率、运行时间、边界失败或业务缺陷。若没有实证缺陷，不因为“创新”或“高级”而升级复杂度。

不同 formulation 才是真正有价值的反事实。仅同一 formulation 换 GA/PSO、改超参数，不算结构性不同。

### Step 3：读取竞赛建模经验

先读 `production/modeling.md` 检查大道至简、参数意义、真实 baseline、优化模型完整性、统计诊断和“小巧思”是否适用。该文件提供经验，不覆盖 modeling constitution 和 structural innovation。

### Step 4：最后按需查 model catalog 并选择 solver

只有 formulation 已明确，且确实需要补充候选工具时才读取 `model_catalog.md`：

- 线性/凸结构优先精确优化或解析方法；
- 树/图结构优先利用图算法和动态结构；
- 大规模组合问题再考虑分解、启发式或近似；
- 预测问题可选择统计/ML，是否为主模型由数据和泛化证据决定；
- 黑箱与复杂模型只有在可验证地解决简单 baseline 缺陷时保留。

模型目录是工具书，不是路由器。

### Step 5：决策记录与命名

每个候选至少记录结构依据、变量、目标/约束、近似/分解、风险、baseline、验证计划与 retain/reject。名称只写真正进入公式、代码或实验的机制；标准模型使用标准名称。

### Step 6：Toy / 解析 sanity check

优先使用最小真实切片、手算 case、解析解、上下界或覆盖关键约束的合成 sanity case。合成 case 仅用于验证实现，不得冒充题目数据。

### Step 7：创新候选进入 DAG benchmark

只有 `adopt for testing` 的候选才通过 `task_dag.py replan` 插入 baseline/proposed/compare 或 ablation：

```text
                 ┌─ baseline-solve ─────┐
TQi-model ───────┤                      ├─ innovation-compare ─ verify ─ write
                 └─ proposed-solve ─────┘
```

输入和指标必须公平。推荐 A 负责结构/formulation，B 负责实现，C 或另一角色独立比较。Stage 3 最多标记 `tested/adopted`，经过 Stage 5/6 的量化比较与 failure test 后才能 `verified`。

### Step 8：跨子问题协调与 red-team

核对 Qi 之间的数据接口、单位、误差传播和共享口径。championship 模式重点攻击关键近似、全局最优区、被忽略耦合、数据泄漏、复杂模型是否真的超越简单 baseline，不凑数量。

## 写入状态

```json
{
  "candidate_formulations": [],
  "candidate_models": [],
  "selected_per_subproblem": {},
  "innovation_decisions": [],
  "rejection_log": [],
  "toy_demos_passed": true,
  "red_team": [],
  "model_family_consistency": "..."
}
```

## L1 Rubric

| 维度 | 满分行为 |
|---|---|
| 题目契约 | 定义、单位、约束未被便利性替换 |
| 结构与 formulation | 先处理结构机会，再选算法 |
| 简单 baseline | 有公平基线；复杂度升级有缺陷证据 |
| 命名真实性 | 所有修饰词能定位到公式/代码/实验 |
| 求解可行性 | toy/解析 sanity check 通过 |
| 可验证性 | 创新候选有 baseline、风险、guard 与后续任务 |

## 退出条件

1. 每 Qi 的 problem contract 与 structure scan 已处理；
2. 最简单可行 formulation 和 baseline 已记录；
3. 若升级复杂度，有明确缺陷证据；
4. 主 formulation、模型与 solver 均有理由；
5. toy/sanity check 通过；
6. adopted innovation candidates 已进入可验证 DAG，或明确没有候选；
7. L1 达到工作流阈值。
