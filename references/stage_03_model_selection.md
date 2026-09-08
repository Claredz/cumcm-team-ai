---
stage: 3
name: model_selection
duration_h: 2-3
inputs:
  - "stage.2.{decomposition, objective_per_subproblem, data_schema, structure_scan, innovation_opportunities}"
outputs:
  - "stage.3.{candidate_formulations, candidate_models, selected_per_subproblem, rejection_log, toy_demos_passed, innovation_decisions, red_team, model_family_consistency}"
loads_reference:
  - "references/structural-innovation.md"
  - "references/model_catalog.md"
  - "references/rubrics.md§Stage_3"
  - "competitions/<comp>/winning_patterns.md§4"
loads_template: ["templates/shared/code_starter/<problem_type>.py"]
feedback: ["L1", "counterfactual_exploration_in_championship"]
next: stage_04_foundation
---

# Stage 3 — 从问题结构到模型与求解器

> v2 适配：本页为导入参考。执行前以根 SKILL.md 和 references/integration-policy.md 为准。默认自主推进；模型复杂度和算法数量不是质量代理。

**时长**: 2-3h | **反馈层**: L1 + 反事实探索

## 目标

为每个子问题先确定**问题表示与 mathematical formulation**，再选择模型族和 solver。必须消费 Stage 2 的 `structure_scan`，不能直接从关键词跳到算法目录。

默认顺序：

`structure → representation/formulation → approximation/decomposition → solver/algorithm`

创新优先发生在问题表示、结构利用和求解策略层；标准模型若最适合，就使用标准名称。

## 产出

- 每个 Qi 的结构处理决定：哪些机会 adopted/rejected，为什么；
- 候选 formulation 与合理替代；
- 主模型、求解器与选型理由；
- 最小可执行 toy demo；
- 若采用结构创新候选，则产生可验证的 baseline/proposed 计划；
- championship 模式的 red-team 证据。

## 操作流程

### Step 0：先读 structure scan

对 Stage 2 每个结构机会逐项做：

```text
I1: candidate → adopt for testing / reject
依据: ...
若采用，它改变的是：变量 / 约束 / 可行域 / 分解 / 求解策略 / 数据机理边界
风险: ...
需要的 baseline/guard: ...
```

`candidate` 不是论文创新点。没有值得采用的机会时正常进入标准模型选择。

### Step 1：先问能否解析、化简或重参数化

在打开算法目录前依次检查：

1. 是否存在解析关系、守恒量、上下界、单调性、凸性或对称性？
2. 是否有中间量可以消去，或通过无量纲化/相对量简化？
3. 是否可以分块、解耦、松弛或按图/树结构局部计算？
4. 是否能使用 coarse-to-fine、剪枝、局部化或 warm start 缩小求解域？
5. 已知机理与数据驱动的边界在哪里？如果使用 ML，是否更适合拟合 residual/unknown term？

这些检查形成 `candidate_formulations`，而不是先形成算法名单。

### Step 2：候选 formulation 比较

每个候选记录：

```text
Formulation F1
- 结构依据：题面/公式/数据中的什么性质
- 决策变量与状态变量：...
- 目标与约束：...
- 近似/消元/分解：...
- 可能引入的误差或遗漏：...
- 可验证基线：...
- 结论：retain / reject
```

不同 formulation 才是真正有价值的反事实。仅同一 formulation 换 GA/PSO 不算结构性不同。

### Step 3：最后选择模型族和 solver

只有 formulation 明确后才读取 `model_catalog.md`。选择能最直接求解当前结构的工具：

- 线性/凸结构优先精确优化或解析方法；
- 树/图结构优先利用图算法和动态结构；
- 大规模组合问题再考虑启发式或分解；
- 预测问题可选择统计/ML，但不得无理由丢弃已知结构；
- 黑箱与复杂模型只有在可验证地解决了简单模型的缺陷时才保留。

候选必须解决同一任务并能公平比较。没有合理替代时记录检索范围，不凑数。

### Step 4：选型决策矩阵

维度建议：问题适配、结构利用程度、求解可行性、时间预算、可验证性、理论/文献支持。分数只是记录工具，不能覆盖明确的数学错误或错误假设。

### Step 5：可核验命名

名称只写已经进入公式、代码或实验的机制。若只实现标准模型，就使用标准名称。不得为了显得创新添加“改进、自适应、多层、融合”等修饰词。

### Step 6：Toy demo / 解析 sanity check

优先使用能暴露关键约束与失败模式的最小真实切片或合成 sanity case：

```python
case = build_representative_case(problem_data, cover=critical_constraints)
model = build_model(case)
result = solve(model, time_budget=remaining_stage_budget)
assert result.status in accepted_statuses
assert constraints_hold(result, case)
```

如有解析解、上下界或手算 toy case，必须拿来交叉验证数值结果。

### Step 7：创新候选进入 DAG benchmark

只有被 `adopt for testing` 的 innovation opportunity 才允许通过 `task_dag.py replan` 插入实验任务。例如：

```text
                 ┌─ baseline-solve ─────┐
TQi-model ───────┤                      ├─ innovation-compare ─ verify ─ write
                 └─ proposed-solve ─────┘
```

baseline 与 proposed 必须使用公平输入和指标。推荐 A 负责结构/公式，B 负责实现，C 或另一角色独立比较。不得同一执行者提出、实现、复核并自行宣布收益。

创新候选在此阶段最多是 `tested/adopted`，只有经过 Stage 5/6 的量化比较和定向攻击后才能标记 `verified`。

### Step 8：跨子问题协调

检查不同 Qi 的模型接口、单位、误差传播和数据结构。为统一工具而牺牲问题适配度时回退重评。

### Step 9：championship red-team

提出能真正改变选型结论的攻击，例如：

- 关键近似不成立；
- coarse stage 裁掉最优区；
- 分解忽略了实质耦合；
- ML 增益来自泄漏；
- 复杂模型没有超越简单 baseline。

每项给证据需求和当前状态，不凑数量。

## 写入状态

```json
{
  "candidate_formulations": [],
  "candidate_models": [],
  "selected_per_subproblem": {},
  "innovation_decisions": [
    {"id": "I1", "decision": "test|reject", "reason": "...", "dag_tasks": []}
  ],
  "rejection_log": [],
  "toy_demos_passed": true,
  "red_team": [],
  "model_family_consistency": "..."
}
```

## L1 Rubric

| 维度 | 满分行为 |
|---|---|
| 结构与 formulation | 先处理结构机会，再选算法；保留合理反事实 |
| 选型理由 | 每候选有适配证据和拒绝理由 |
| 命名真实性 | 所有修饰词都能定位到公式/代码/实验；允许标准名称 |
| 求解可行性 | toy/解析 sanity check 通过 |
| 可验证性 | 创新候选有公平 baseline、风险和 guard 计划 |

## 常见坑

- 看到题型关键词就直接选 GA/LSTM；
- 把换 solver 当作 formulation 创新；
- `A+B+C` 组合却说不清每个组件解决什么困难；
- 为显得创新强行改名；
- 没有 baseline 就声称“显著提升”；
- 为了寻找创新把原本简单可解的问题复杂化。

## 退出条件

1. 每 Qi 的 structure scan 已被处理；
2. 主 formulation、模型与 solver 均有证据；
3. toy/sanity check 通过；
4. adopted innovation candidates 已进入可验证 DAG 任务，或明确没有候选；
5. championship red-team 的实质风险有证据动作；
6. L1 达到工作流阈值。
