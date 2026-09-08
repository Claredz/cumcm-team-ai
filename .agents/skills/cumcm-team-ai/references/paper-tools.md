# 完整论文生产与 LaTeX 工具

由 production/writing.md/visualization.md 提供章节论证、摘要、图表和版面经验；实际编译用 templates/latex/<comp>/main.tex。不要将上游 cumcmthesis 或固定 21—30 页作为依赖。三赛事装配模板需要 01—10 章节；无适用灵敏度内容时解释不适用的理由，不凭空造实验。

输入 paper_workspace/：01_abstract.md、02_problem_restate.md、03_analysis.md、04_assumptions.md、05_notation.md、06_models.md、07_sensitivity.md、08_evaluation.md、09_references.md、10_appendix.md。最后一项应包含运行代码/文件列表，引用与结果来自已核验产物。

使用实际标题、关键词、题号与赛事要求的控制号填入 decision_log.paper_metadata。模板检测缺失章节、重复/未知标记和提交元数据占位符；正式渲染先导出 AI 台账。国赛 2026 的使用/未使用声明位于参考文献之前，使用详情在支撑材料；美赛报告在正文限页范围之后。

```bash
python <skill>/scripts/render_paper.py --competition cumcm --workspace <project>/paper_workspace --decision-log <project>/state/decision_log.json --output-dir <project>/paper_output
python <skill>/scripts/render_paper.py --competition cumcm --workspace <project>/paper_workspace --decision-log <project>/state/decision_log.json --output-dir <project>/paper_output --engine /path/to/tectonic
python <skill>/scripts/pdf_audit.py <project>/paper_output/main.pdf --competition cumcm --render-dir <project>/paper_output/pages --output <project>/state/pdf-audit.json
```

中文模板默认 CTeX+Fandol，英文默认 pdfLaTeX。Tectonic 为可选单程序替代并自动处理多遍编译，首次可能下载 TeX 资源；传 --compile-timeout 可设置单次时间上限，赛前预热缓存。doctor.py --engine /path/to/tectonic 可核查其可执行文件，资源包实际可用性通过编译验证。编译失败修复具体错误后重编，不把旧 PDF 当新输出。Pandoc 负责正式 Markdown 转换；简化转换仅供 --no-compile 结构检查。

工具依赖：Python requirements.txt；Pandoc 可系统安装或通过 pypandoc_binary 提供可执行文件；TeX 使用已有 XeLaTeX/pdfLaTeX 或 Tectonic，不必全量安装多个引擎。参考图模板位于 templates/diagrams/，需要 TikZ 时加载 pgf/tikz；架构图应反映真实数据依赖。

PDF 审查计页以正文与附录边界为准；自动找不到边界时给出 review，使用 --body-start/--body-end 明确页码。不将“PDF 生成成功”视为匿名、语义、图表可读性和比赛合规全通过。渲染页面后检查溢出、断字、符号、图例与摘要；自动密度只提示，不强制凑图。
