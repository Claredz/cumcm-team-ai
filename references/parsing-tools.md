# 题面与题型解析

运行 `python <skill>/scripts/parse_problem.py problem.pdf --attachments data.xlsx data.csv --output <project>/state/problem-package.json`。

支持 PDF 文本页、DOCX 段落/表格、UTF-8 文本、Markdown，附件 CSV/XLSX 列名和行数。输出题面 SHA256、每页原文、候选分问的页行位置、关键词支持的题型候选、附件清单和错误。扫描/稀疏 PDF 会标记需要 OCR/视觉核对，不将空文本视为读题成功。

脚本负责提取，AI 负责语义：检查候选分段是不是题目小问而非参考文献/枚举；补齐没有显式编号的任务；核对公式、图、单位、约束、输出文件与小数位。完成后填 objective、constraints、deliverables、depends_on 和 semantic_reviewed；确认所有分问后再写 question_count。

题型可混合，例如预测+优化；保留实际触发证据。按题面而非题号选择模型目录。DOCX 方程对象、图片和 PDF 排版复杂处必须视觉检查。没有 OCR 工具时报告具体页面，继续处理可读部分，不编造公式。

将题目包映射到 decision_log.stages.2.decomposition/data_schema。上游输出依赖必须有题面或模型依据，不能为了“统一”强行依赖。详读 production/parsing.md 的完整拆题协议；其工具可用性以实际环境为准。
