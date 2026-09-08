# 结构性创新协议

本页定义数学建模竞赛中“创新”的默认含义与执行方式。核心原则：**创新优先发生在问题表示、结构利用和求解策略层，而不是算法名称层。**

## 1. 先定义什么不算创新

以下内容默认不构成可声明的创新，除非有问题特定机制与对比证据：

- 仅把多个标准算法串起来、拼接后重新命名；
- 只改超参数、迭代公式或随机初始化，而问题结构未发生变化；
- 为标准模型增加“改进、自适应、多层、融合”等修饰词；
- 仅因为模型冷门、复杂或使用了神经网络/元启发式，就声称更创新；
- 没有 baseline、消融或可复核证据的“精度更高、效率更好、鲁棒性更强”。

标准模型若最适合，应使用标准名称。0 个真实创新优于多个伪创新。

## 2. 结构扫描：在选算法前先问这些问题

对每个子问题，先检查下列结构机会；找不到时明确记录 `none`，不得强行制造：

1. **假设与降维**：是否存在有依据的近似、尺度分离、对称性或低维表示，使自由度减少？
2. **机理与已知结构**：是否存在守恒、几何、动力学、概率、图结构、单调性、凸性或稀疏性可直接利用？
3. **消元与重参数化**：是否有难求但不必显式求出的中间量？能否通过消元、比值、无量纲化、坐标变换或充分统计量绕开？
4. **解耦与分解**：耦合是否只集中在少量变量或约束？能否通过分块、动态规划、拉格朗日松弛、分解协调等方式拆成独立或弱耦合子问题？
5. **coarse-to-fine**：能否先用便宜的近似模型、粗网格或低精度仿真定位候选区域，再做精细求解？
6. **搜索空间压缩**：能否利用上下界、单调性、支配关系、剪枝、局部化、多精度离散或 warm start 避免全域暴力搜索？
7. **灰箱边界**：已知机理能解释多少？若数据驱动不可避免，能否让 ML 只拟合残差、未知项或参数，而不是无理由丢弃已知结构？
8. **解析基线**：是否存在解析解、极端情况、上下界、简化模型或可手算 toy case，可用于约束和验证数值算法？

Stage 2 的输出应包含每个子问题的 `structure_scan`，Stage 3 必须消费该结果后才进入 solver/algorithm 选择。

## 3. Innovation opportunity 不是 innovation claim

结构扫描发现的候选只记为 hypothesis：

```json
{
  "id": "I1",
  "subproblem": "Q3",
  "type": "coarse_to_fine",
  "observation": "全域高精度搜索计算量过高，简化模型可定位窄候选区",
  "proposed_change": "先用近似模型圈定区域，再局部精细求解",
  "expected_benefit": "降低搜索规模和运行时间",
  "risk": "粗模型可能裁掉真实最优区",
  "evidence_needed": "full-domain baseline + 局部方法 + 全域抽查"
}
```

状态至少区分：`candidate | tested | adopted | rejected | verified`。未经验证不得在摘要或模型名称中包装为创新。

## 4. 结构创新的主要模式

### 4.1 有依据的假设与降维

好的假设应同时回答：

- 为什么现实上可接受；
- 它删除或合并了什么自由度；
- 它使什么数学结构变得可解；
- 放松假设时主要结论变化多少。

“忽略某项”本身不是创新；**由合理近似产生可验证的结构简化**才可能成为创新。

### 4.2 机理优先，但不强迫伪机理

默认原则是“利用已知结构优先于无结构拟合”，而不是“机理模型永远优于机器学习”。

推荐顺序：

`解析结构 / 简化机理 → 统计模型 → 黑箱模型`

若机理只能解释一部分，可使用：

`mechanism + residual learner`

并与 `mechanism-only`、`data-only` 做消融比较。

### 4.3 coarse-to-fine / 多精度

典型链：

`cheap approximation → candidate region → accurate solver`

必须验证粗阶段没有错误裁掉优区。可使用边界扩张、多起点、随机全域抽查或近似误差界作为 guard。

### 4.4 消去难求中间量

优先寻找：

- 代数消元；
- 重参数化；
- 无量纲化；
- 相对量或比值；
- 不变量、守恒量；
- 充分统计量；
- 对偶变量或替代表达。

验证时检查：消元是否引入奇点、额外解、不可逆条件或边界遗漏。

### 4.5 求解规模压缩

可包括：

- 枚举剪枝与支配规则；
- 从局部/已知结构逐层扩展，而非全域枚举；
- 问题解耦与分块；
- 拉格朗日松弛或其他可解释分解；
- 粗网格到细网格；
- 利用上下界、凸性、单调性、稀疏性；
- 有依据的 warm start 与局部化。

复杂度下降本身可以是重要建模贡献，但必须记录规模、运行时间和质量损失。

## 5. 算法组合何时才有意义

组合不是因为“模型越多越好”，而是每个组件解决另一个组件的明确困难。至少满足一种：

- A 缩小 B 的搜索空间；
- A 提供 B 的初值、参数、边界或候选集；
- B 修正 A 的系统残差；
- A 与 B 处理不同尺度或不同约束层；
- 两者的误差具有经验证的互补性。

无法说明接口和因果作用的 `A+B+C` 默认视为堆砌。

## 6. 每个可声明创新必须可证伪

最终 innovation claim 必须回答：

1. **Problem**：直接/常规做法具体卡在哪里？
2. **Change**：我们改变了问题表示、假设、分解或求解策略的什么？
3. **Mechanism**：为什么这个改变理论上应当有效？
4. **Baseline**：不用该改变时的公平基线是什么？
5. **Evidence**：精度、目标值、可行率、规模、运行时间等至少一项量化对比；必要时给消融。
6. **Risk/guard**：创新可能在哪些条件下失败，做了什么保护测试？

推荐结构：

```json
{
  "problem": "full-domain search is expensive",
  "change": "coarse model narrows the candidate region before exact search",
  "mechanism": "the approximation preserves the dominant geometry in the tested domain",
  "baseline": "full-domain solver",
  "proposed": "coarse-to-fine solver",
  "metrics": {"runtime_s": {"baseline": 487.2, "proposed": 61.4}, "objective_gap": 0.0027},
  "risk": "coarse model may discard the global optimum region",
  "guard": "expanded region + random global probes"
}
```

只有 `verified` 的 innovation claim 才能进入摘要和“创新点”表述。

## 7. DAG 执行协议

Stage 2 后仍以 task DAG 为实际调度中心，不新增固定的“创新阶段”。默认 `TQi-model` 读取 `structure_scan`，逐项 `adopt/reject`。

只有当某个候选值得验证时，使用 `task_dag.py replan` 动态插入 benchmark/ablation 任务，例如：

```text
                 ┌─ baseline-solve ─────┐
TQi-model ───────┤                      ├─ innovation-compare ─ verify ─ write
                 └─ proposed-solve ─────┘
```

推荐职责分离：A 负责结构/公式，B 负责 baseline 与 proposed 实现，C 或另一角色负责独立比较和证据核验。不得由同一执行者提出、实现、复核并自行宣布收益。

## 8. Stage 6 对创新做定向攻击

不同创新模式需要不同 failure-oriented test：

| 类型 | 必查风险 |
|---|---|
| 假设/降维 | 放松假设后核心结论是否改变 |
| coarse-to-fine | 是否裁掉全局优区 |
| 剪枝 | 被剪分支为何不可能产生更优/可行解 |
| 解耦/松弛 | 被弱化的耦合残差与对偶/可行性误差 |
| 消元/重参数化 | 奇点、额外解、不可逆区间 |
| 近似机理 | 近似误差随状态/参数何时失效 |
| 灰箱 | mechanism-only / data-only / hybrid 消融 |

若测试推翻创新，不必推翻整个主模型；把该 innovation opportunity 标记为 `rejected`，保留失败证据。

## 9. 写作与终审

论文中的创新叙事固定遵循：

`原方法困难 → 结构观察 → 改变 → 机制 → baseline 对比 → 量化收益 → 适用边界`

摘要只允许引用已验证结果。不得把 `candidate/tested/rejected` 写成“本文创新性提出”。

最终原则：**少而真、可复核、能说明为什么有效。** 对多数国赛论文，0–2 个真正结构性贡献通常比多个算法修饰词更可信；这不是数量硬门槛。
