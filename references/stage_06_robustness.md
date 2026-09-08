---
stage: 6
name: robustness
duration_h: 2-3
inputs:
  - "stage.5.sub_problems.{Qi}.{code_path, key_metrics}"
  - "stage.4.{assumptions, symbols}"
  - "stage.3.{selected_per_subproblem, innovation_decisions}"
outputs:
  - "stage.6.{params_varied_jointly, method, deltas, robust_intervals, stability_verdict, innovation_tests, failure_warning, L2_backtrack, figures}"
loads_reference:
  - "references/structural-innovation.md"
  - "competitions/<competition>/winning_patterns.md"
  - "references/rubrics.md"
  - "competitions/<competition>/anti_patterns.md"
loads_template:
  - "templates/shared/code_starter/simulation.py"
  - "templates/shared/sensitivity_table.md"
feedback: ["L1", "L2_cross_stage"]
next: stage_07_evaluation
---

# Stage 6 — 验证、灵敏度、稳健性与创新攻击

> v2 适配：本页为导入参考。执行前以根 SKILL.md 和 references/integration-policy.md 为准。不同题目使用不同验证方法；参数数量、图数、采样算法都不是质量代理。

## 目标

检查核心结论在合理不确定性、数据切分、随机性与边界条件下是否仍成立；同时对 Stage 2/3 中采用的结构性创新做**定向 failure-oriented test**。创新候选若被推翻，允许只撤销该创新而保留主模型。

## 输入

- Stage 5 各子问题的求解代码、结果与复现入口；
- Stage 4 的关键假设、参数来源、符号与单位；
- Stage 3 的模型选择与 `innovation_decisions`；
- benchmark/ablation 任务产生的 baseline/proposed 证据。

## 产出

- 核心结论的风险清单与验证设计；
- 扰动范围、数据切分和场景依据；
- 关键指标、决策变化和失败样本；
- 每个 adopted innovation 的定向攻击结果；
- `verified | rejected | still_unverified` 的创新状态；
- 对 Stage 3/4/5 的 L2 回检。

## Step 1：先列风险，再选方法

对每个核心结论问：什么变化最可能让它失效？覆盖真正相关的风险：参数不确定性、数据漂移、随机性、模型结构、离散边界、算法近似、依赖结果漂移等。

只验证会影响主要结论的风险；未覆盖项进入 Stage 7 limitations，不用无关扰动凑数量。

## Step 2：按风险匹配验证方法

- 单主导参数：OAT、局部导数、剖面分析；
- 多参数交互：因子设计、LHS、联合抽样；
- 时间/空间数据：滚动验证、分组留出、外推测试；
- 随机算法：多种子、重复实验、置信区间；
- 优化模型：系数/RHS 扰动、替代最优解、可行性压力测试；
- 离散制度变化：情景枚举、边界扫描；
- 模型结构风险：替代 formulation、消融、解析边界或反例测试。

方法没有等级顺序，按风险和预算选择。

## Step 3：用证据确定范围和判断标准

优先使用测量精度、置信区间、历史分位、物理可行域、业务规则或题目边界。只能假设时明确标记 `scenario_assumption`。

在看结果前写清：baseline、指标与单位、可行性/误差边界、决策变化度量，以及什么情况触发回退。

## Step 4：对 adopted innovation 做定向攻击

逐项读取 `references/structural-innovation.md` 和 Stage 3 的 innovation decision。

| innovation type | 必查 failure mode | 最低证据 |
|---|---|---|
| 假设/降维 | 放松假设后核心结论改变 | relaxed model / sensitivity 对比 |
| coarse-to-fine | 粗阶段裁掉真实优区 | 全域抽查、多起点、扩张候选区或误差界 |
| 剪枝/支配 | 被剪分支仍可能可行/更优 | 剪枝条件证明或反例搜索 |
| 解耦/松弛 | 被忽略耦合过大 | residual、duality/feasibility gap |
| 消元/重参数化 | 奇点、额外解、不可逆区间 | 边界/逆映射检查 |
| 近似机理 | 近似在某区间系统失真 | approximation error profile |
| 灰箱/混合 | 增益只是复杂度或泄漏 | mechanism-only / data-only / hybrid 消融 |
| 搜索空间压缩 | 缩小范围造成质量损失 | full/expanded-domain baseline 抽查 |

每个创新测试输出：

```json
{
  "innovation_id": "I1",
  "baseline": "...",
  "proposed": "...",
  "metrics": {},
  "failure_test": "...",
  "result": "verified|rejected|still_unverified",
  "risk_boundary": "...",
  "evidence_paths": []
}
```

判定原则：

- `verified`：公平 baseline + 量化收益/结构收益 + 关键 failure test 均有证据；
- `rejected`：结构假设或收益被反例/实验推翻；
- `still_unverified`：证据不足，不得写入摘要创新点。

## Step 5：运行并保留可复核记录

保存运行入口、随机种子、环境版本、输入版本、失败样本和异常处理。预测/统计任务使用正确的数据切分，不为了复用代码而强行扰动参数。

## Step 6：只画能回答风险问题的图

图应回答非线性、阈值、场景差异、漂移、可行域切换、创新 baseline 对比等具体问题。每张图写清样本、范围、指标和证据路径。

## Step 7：报告范围与失败边界

写清：

- 已测试域内核心指标怎样变化；
- 哪些结论稳定，哪些只局部成立；
- 是否出现不可行、误差超限或方案切换；
- adopted innovation 在什么条件下仍有效；
- 测试域之外不能推断什么。

没有观察到边界时写“在已测试域内未发现失败边界”，不要虚构临界点。

## Step 8：L2 跨阶段回检

检查：

1. Stage 3 的 formulation/solver 选择是否仍有证据；
2. Stage 4 的关键假设是否被挑战；
3. Stage 5 上游结果复用是否仍有效；
4. 哪些 innovation candidate 应转为 verified/rejected/still_unverified；
5. 是否需要 invalidate/replan DAG 下游任务。

如核心结构被推翻，调用 `task_dag.py invalidate/replan` 级联重算；如果只是创新收益不成立，可撤销创新表述而保留主模型。

## 写入状态

```json
{
  "params_varied_jointly": [],
  "method": "...",
  "deltas": [],
  "robust_intervals": {},
  "stability_verdict": "...",
  "innovation_tests": [],
  "failure_warning": "...",
  "L2_backtrack": {},
  "figures": []
}
```

## L1 Rubric

| 维度 | 满分行为 |
|---|---|
| 验证设计 | 方法针对真正核心风险 |
| 范围真实性 | 扰动/切分/场景有来源 |
| 输出完整 | 性能、决策、可行性与失败样本中适用部分齐全 |
| 定量可复核 | 样本、种子、区间、判断标准和证据路径完整 |
| 创新与边界 | adopted innovation 有定向攻击；未验证/失败不包装为创新 |

## 常见坑

- 统一用 ±10% 灵敏度替代真正风险；
- 只比较 proposed 的最好一次运行；
- coarse-to-fine 不检查是否裁掉全局优区；
- 剪枝没有证明/反例检查；
- 混合模型没有 component ablation；
- innovation 失败后仍保留摘要中的“显著提升”。

## 退出条件

1. 核心结论至少有一种风险匹配的验证；
2. 范围与判断标准可追溯；
3. adopted innovation 全部得到 `verified/rejected/still_unverified` 状态；
4. 结果包含定量变化和适用边界；
5. L2 回检完成并处理需要的 DAG invalidation；
6. L1 达到工作流阈值。
