# 阶段 3-4：代码实现与求解

> v3 适配：执行前以根 `SKILL.md`、`modeling-constitution.md` 和 `integration-policy.md` 为准。核心是：**真实输入 + 可复现路径 + 增量纠错 + 代码/论文一致**。固定图数和个人绝对路径不再作为硬要求。

## 1. 数据真实性红线

不得用未标注的合成数据替代题目提供的真实数据。以下行为直接视为高风险：

- 题目给了附件，却在正式求解代码里完全不读取附件；
- 自行生成随机样本并把结果当作真实观测；
- 假设不存在的 `data.csv`、列名或单位；
- 为了让模型跑通而默默补造标签。

随机数本身不是错误。蒙特卡洛、bootstrap、随机重启、仿真、交叉验证拆分和测试夹具都可以使用随机数，但必须说明用途、设置随机种子，并与真实输入边界区分。

## 2. 路径规则：可复现优先，不硬编码个人绝对路径

正式脚本通过 `--workspace`、config 或 data manifest 从项目根定位文件。推荐：

```python
from pathlib import Path
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[1])
args = ap.parse_args()
root = args.workspace.resolve()
data_file = root / "data" / "raw" / "附件1.xlsx"
result_dir = root / "runs" / "Q1"
result_dir.mkdir(parents=True, exist_ok=True)
```

运行时可以把 `data_file.resolve()` 写进日志用于诊断；但不得把 `/home/name/...`、`C:\\Users\\name\\...` 写死进最终脚本、论文或支撑材料。

如果项目结构不是固定 `data/raw`，将真实相对路径写入 manifest，例如：

```json
{"files":[{"id":"attachment_1","path":"data/raw/附件1.xlsx","sha256":"..."}]}
```

求解脚本按 id 读取。这样工作区换机器仍可复现。

## 3. 求解上下文

每问的执行上下文至少包含：

```text
问题 Q{idx}: {rephrased}
题目契约: 输出、单位、官方定义、约束
最终 formulation: {chosen_formulation}
结构决策: adopted/rejected opportunities
真实数据 manifest: {relative paths + schema + units + hashes when frozen}
baseline / proposed: {if any}
acceptance: {constraints, metrics, sanity checks}
```

不要只给编程手一个算法名。

## 4. 写码 → 运行 → 增量修复

首版代码应完整可运行。后续报错优先 Search-Replace / 局部编辑，不反复重写整个长文件，避免把已经正确的部分改坏。

推荐修复顺序：

1. 复现错误并保存 stdout/stderr；
2. 定位最小失败位置；
3. 只改相关函数/参数/路径；
4. 重跑原 case；
5. 再跑 regression/sanity case；
6. 若同一故障连续出现，回到 formulation/数据假设检查，而不是无限 patch。

不使用固定“10 轮必停”作为竞赛规则；按剩余时间、故障重复性和风险决定是否换思路。

## 5. 每个 solve task 的可复现清单

- [ ] 读取真实 data manifest / workspace-relative 文件；
- [ ] 输入 schema、单位、缺失处理有记录；
- [ ] 随机性有用途说明与 seed；
- [ ] 配置、模型参数、solver status 与运行环境进入 run log；
- [ ] 关键结果写入机器可读 JSON/CSV，而不是只 print；
- [ ] headline number 能被 `claim_registry.py` 绑定到 source field；
- [ ] 需要的图来自同一 run 结果，不重新手工造数字；
- [ ] 代码可由新的工作区路径重跑；
- [ ] 约束、量纲、边界或解析/toy sanity check 通过。

图的数量由论文信息需求决定。每张图应回答不同问题；没有信息价值的图不因“至少 5 张”而生成。

## 6. 结果组织

推荐每问：

```text
runs/Q1/<run_id>/
  config.json
  stdout.log
  metrics.json
  result.csv
  figures/
  environment.json
```

论文使用的关键数值进入 claim registry；DAG receipt 记录产物和 SHA。需要人工阅读的 `solve_summary.md` 可以从机器可读结果生成，但 summary 不是权威数值源。

## 7. baseline 与创新实验

如果 Stage 3 插入 baseline/proposed：

- 使用相同输入切分、约束口径和评价指标；
- 记录 wall time、solver status、objective/误差、可行率和必要的资源信息；
- 不为了让 proposed 好看而给 baseline 更差超参数或更小预算；
- coarse-to-fine、剪枝、解耦等结构创新要额外记录 guard/failure test；
- 若 proposed 没有优势，保留结果并撤销创新表述。

## 8. 独立复算与代码—论文一致

关键结果不能只通过“再运行同一函数一次”验证。由不同角色/脚本按 `verification.md` 和 `verify_independence.py` 做结构独立复核。

交付前核对：

- 论文公式 ↔ 实现；
- 初始化、邻域、停止条件、随机种子 ↔ 实际代码；
- 摘要/正文/表格的关键数字 ↔ claim registry/source field；
- 单位与口径 ↔ 题目契约；
- 附录/支撑材料 ↔ 最终运行代码，不手抄旧版本；
- 数据文件相对路径与 README/manifest 一致。

## 9. 求解交付清单

- [ ] 每个必要 `solve.py`/notebook 可按 README 命令运行；
- [ ] 无未标注假数据；
- [ ] 无个人机器硬编码路径；
- [ ] 关键结果有机器可读源和 run log；
- [ ] 关键 claim 已验证；
- [ ] 图表与正文数字来自同一冻结 run；
- [ ] 上游变化后相关 DAG task 已 invalidate/recompute。
