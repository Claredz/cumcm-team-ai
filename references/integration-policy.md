# 导入资料适配规则

本包整合 LEEHAHAHAHA 的六类生产指南/TikZ 经验与 handsomeZR-netizen 的阶段、反馈、赛事、模型目录和工具。来源见 THIRD_PARTY_NOTICES.md。导入文件保留其经验价值，但不自动取得与根 skill 同等权威。

## 权威层级

发生冲突时按下列顺序解释：

1. 当届官方规则与赛题原文；
2. `references/modeling-constitution.md`；
3. `references/structural-innovation.md`；
4. `references/production/modeling.md` 的竞赛建模经验；
5. `references/model_catalog.md`（formulation 明确后按需查）；
6. 版面、图数、公式数、页数、配色等经验 heuristic。

workflow、DAG、评分器和模型目录都不能覆盖更高层的数学事实与题面契约。

## 具体覆盖规则

1. 默认 autonomous；旧文档的强制编号问答和每次评分后确认只适用于 guided 模式。例行修错、参数试跑、章节整理由 AI 执行，关键事项集中交接。
2. high issue 阻止产物放行，先自动修复重跑；实质缺输入或需要队员判断才询问。不得删除问题记录来伪造通过。
3. 固定图数、公式数、最低页数、caption 字数、图占比和统一字体只作建议，不构成阻断。官方上限、文件规范和真实损坏属于 hard gate。`scripts/check_layout.py` 对这类经验阈值默认只输出 hint/review；只有显式 hard limit 或乱码等确定性错误才失败。
4. 创新协议以 `structural-innovation.md` 为准：先扫描问题结构，再决定 formulation 和 solver；算法数量、冷门程度、拼接或命名不构成创新证据。允许没有创新点。
5. “机理优先”解释为“利用已知结构优先于无结构拟合”，不是强制所有题建立伪机理。数据驱动任务允许 ML 作为主模型，但必须有真实泛化、泄漏与解释/消融检查。
6. **路径可复现优先。** 项目代码使用 workspace-relative path、CLI 参数、config 或 manifest 定位真实数据；运行日志可以记录解析后的绝对路径用于诊断。不得把 `/home/...`、`C:\Users\...` 等个人路径硬编码进最终脚本、论文或支撑材料。
7. 架构图规范以 `references/architecture-diagram.md` 为准，模板为 `templates/diagrams/architecture.tex`，重叠检查为 `scripts/diagrams/check_overlap.py`。保留 `skills/tikz-architecture-diagram/` 作为旧文档兼容入口，但不形成第二套规则。
8. 各问流程图以 `templates/diagrams/flow_snake.tex` 和 `production/visualization.md §5.1.1` 的**蛇形横向**布局为准。导入 writing/review 中残留的“纵向 TikZ”字样视为历史文本，不得执行。
9. 国赛采用 `competitions/cumcm/current_rules.md` 的 2026 新规则；旧 2025 AI 位置作废。其他赛事使用各自 current_rules，不套用国赛时长和页数。
10. `state/decision_log.json` 是项目根状态与学术阶段权威；`state/task_dag.json` 在 Stage 2 后仅作为从属任务执行账本。二者通过 `workflow.py status/reconcile` 对账，不允许各自独立解释“项目是否完成”。
11. 假设变化影响解时，应重建/重算依赖模型；不可仅对旧结果重画图。创新候选被推翻时撤销该创新表述并 invalidate 必要下游，不为了“保创新”继续使用错误方案。
12. 经验分位不能自动决定模型数量、论文厚度或奖项。所有语料下载仅赛前、来源许可允许时执行。
13. 论文主线采用三赛事原创装配模板，不依赖 cumcmthesis 类。生产指南提到 cumcmthesis 时仅视为上游写作示例，本包不再分发该类文件。

`fast/standard/championship` 控制反馈深度，`autonomous/guided` 控制交互频率，两者独立。剩余时间不足按实证风险裁剪，不固定在最后若干小时机械扩张代理或复杂度。
