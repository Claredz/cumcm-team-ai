---
name: tikz-architecture-diagram
description: cumcm-team-ai 的论文总体架构图兼容入口。权威规范位于 references/architecture-diagram.md；使用根目录 architecture.tex 与 check_overlap.py，不维护第二套建模或绘图规则。
---

# TikZ 论文总体架构图（兼容入口）

本目录只为兼容已导入的 production 文档与旧调用路径。**权威规范是 `../../references/architecture-diagram.md`。**

当前实现：

- 总体架构图模板：`../../templates/diagrams/architecture.tex`
- 各问流程图模板：`../../templates/diagrams/flow_snake.tex`（蛇形横向）
- 重叠/越界检查：`../../scripts/diagrams/check_overlap.py`

职责边界：总体架构图通常全文 1 张，用于展示论文分层骨架；各问计算步骤使用横向蛇形流程图，不把架构图换标签复制成多张。

旧 `templates/fig.tex` 与 `scripts/check_overlap.py` 路径保留兼容 wrapper。新代码与新文档应直接引用根目录规范和实现。
