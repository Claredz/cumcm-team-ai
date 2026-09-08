# 论文总体架构图协议

本页统一原 `tikz-architecture-diagram` 子 skill 的有效做法，并适配当前仓库路径。它只负责**论文总体架构图**，不负责各问求解流程图。

## 1. 职责边界

| 图 | 默认数量 | 位置 | 实现 |
|---|---:|---|---|
| 论文总体架构图 | 通常 1 张 | 问题分析节末尾 | `templates/diagrams/architecture.tex` |
| 各问求解流程图 | 按需要 | 各问模型建立/求解处 | `templates/diagrams/flow_snake.tex` 的蛇形横向布局 |

判据：表达“全文如何分层组织、各问如何归位”用总体架构图；表达“这一问从输入到输出怎么计算”用流程图。不要把同一张架构图换标签复制成多张。

## 2. 总体架构图的推荐结构

典型五层仅作起点，不是硬模板：

`数据与题面 → 模型/formulation → 算法求解 → 结果输出 → 结论/推广`

每层保留能帮助评委理解论文主线的模块。不要为了“丰满”把所有库名、超参数和中间变量塞进去。

## 3. TikZ 设计原则

- 先确定画布、层带和组件盒坐标，再写文字；避免依赖自动布局造成遮挡。
- 中文字体使用跨平台 fallback；西文优先 Times 风格，但字体不是赛事硬规则。
- 配色可用低饱和 Okabe-Ito 或与全文一致的学术配色；颜色承担层次区分，不承担“越多越高级”的装饰作用。
- 层内组件标题基线一致；组件多时扩宽/分行，不通过压缩字号硬塞。
- 底色和层带先画，文字后画，避免 TikZ 绘制顺序把文字覆盖。
- `text width` 等 TeX 长度用合法维度表达，出现 PGF Math Error 或大量 Overfull 时先查模板参数。

当前模板：`templates/diagrams/architecture.tex`。旧路径 `skills/tikz-architecture-diagram/templates/fig.tex` 仅作兼容入口。

## 4. 构建与核验

Linux / WSL2：

```bash
cp <skill>/templates/diagrams/architecture.tex <project>/paper_workspace/figures/architecture.tex
cd <project>/paper_workspace/figures
xelatex -interaction=nonstopmode -halt-on-error architecture.tex
python <skill>/scripts/diagrams/check_overlap.py architecture.pdf
```

Windows PowerShell：

```powershell
Copy-Item <skill>\templates\diagrams\architecture.tex <project>\paper_workspace\figures\architecture.tex
Set-Location <project>\paper_workspace\figures
xelatex -interaction=nonstopmode -halt-on-error architecture.tex
python <skill>\scripts\diagrams\check_overlap.py architecture.pdf
```

`<skill>` / `<project>` 是文档占位符，实际运行时由 agent 或队员替换成真实路径；路径含空格时使用引号。自动化流程优先直接调用 Python/TeX 可执行文件，不要求 Git Bash。

若环境有 `pdftoppm` / `pdftocairo`，可另外导出 PNG/SVG 预览；没有这些工具也不阻断主流程。PDF 矢量版本优先嵌入论文。

构建后至少检查：

1. `.log` 无 `Missing character`；
2. 无明显 Overfull；
3. `check_overlap.py` 不报告文字越界/严重重叠；
4. 逐页/单图视觉检查确认箭头、文字、盒子与层次关系正确；
5. 图中方法名与论文正文、DAG 和最终模型一致。

`check_overlap.py` 是几何提示，不理解数学含义；密集公式可能产生假阳性，需人工复核。

## 5. 论文嵌入

总体架构图的 caption 应解释“这张图帮助读者看懂什么”，不重复把所有盒子逐字念一遍。上游 100–150 字只是经验值，不是硬门。图应靠近首次讨论位置；是否同页/相邻页可用 `scripts/check_layout.py` 做 advisory lint。

## 6. 兼容说明

为兼容已导入 production 文档，保留 `skills/tikz-architecture-diagram/` 轻量入口；其中规则全部重定向到本页和当前根目录模板/脚本，不维护第二套架构图规范。
