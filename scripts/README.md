# 工具说明

完整的 v2 命令、输入输出和状态契约见 [toolchain.md](../references/toolchain.md)，论文链见 [paper-tools.md](../references/paper-tools.md)，解析见 [parsing-tools.md](../references/parsing-tools.md)。

- doctor.py：包结构、配置、阶段状态及本地依赖检查；--skip-tools 仅结构检查。
- parse_problem.py：带来源定位的题面候选与附件字段提取。
- workflow.py：十阶段 init/status/next/complete/rollback；实际产物摘要和回退记录。
- score_artifact.py：上游 Critic schema 验证、分数重算、逐问聚合、定向修补判定和持久化。原始分数须有证据，CLI 不调用模型。
- extract_diff.py：章节补丁或统一差异应用，保留大段内容，拒绝陈旧上下文。
- render_paper.py：编号 Markdown→三赛事模板→真实 PDF；--engine 可用 Tectonic 路径，--no-compile 为结构预览。
- render_ai_usage.py：国赛 2026 声明位于参考文献前，无论使用/未使用均生成 AI工具使用声明.md；使用时另有详情 PDF。美赛报告写 11_ai_use_report.md；电工杯生成待核对的内部台账。
- pdf_audit.py：赛事页数边界、缺字/溢出等检查、逐页渲染。
- prose_lint.py：中英表达建议和改写的受保护 token 差异，返回 2 代表需检查数字/公式/引用/否定变化。
- corpus.py：官方展廊元数据索引、本地论文去重、提取 QA 和分组分位。
- diagrams/check_overlap.py：从第一个仓库整合的 PDF 文字边界盒重叠/越界提示，运行 `python scripts/diagrams/check_overlap.py figure.pdf`；密集数学符号可能需人工解释。
- ingest_papers.py：保留的上游 pdfplumber 文本统计维护器，不自动覆盖官方或上游经验 JSON。
- download_cumcm_papers.py：保留的上游展廊维护下载器，仅赛前、来源许可允许时用；默认输出当前项目 local-corpus，不写 skill 目录。需 scripts/requirements-maintenance.txt 的额外依赖与 Playwright 浏览器。

AI 台账保留工具、型号/版本（不可见则明确注明）、环节、用途、过程说明或交互、采纳和核验记录。missing/null 不是未使用；不得伪造人工审查。国赛过程说明可用 disclosure 记录，不强制把所有对话全文塞进论文。工具字段比官方最低描述更结构化，属于项目实现，不冒充规则原文。
