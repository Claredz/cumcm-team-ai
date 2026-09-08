# 工具说明

完整命令与状态契约见 [toolchain.md](../references/toolchain.md)，论文链见 [paper-tools.md](../references/paper-tools.md)，解析见 [parsing-tools.md](../references/parsing-tools.md)。平台安装见 [Windows](../references/setup-windows.md) 与 [Linux/WSL2](../references/setup-linux-wsl.md)。

核心脚本以 Python 3.10+、`pathlib` 和跨平台 subprocess 为边界，正式支持 Windows 10/11 PowerShell、Linux 与 WSL2。核心 workflow 不要求 Git Bash；平台专属 shell 命令只用于人工辅助检查，必须在文档中明确标注。

- `doctor.py`：包结构、平台、配置、阶段状态及本地依赖检查；Windows/Linux/WSL 会显示平台标签。
- `parse_problem.py`：题面候选、来源定位与附件字段提取。
- `workflow.py`：十阶段 init/status/next/complete/rollback/reconcile；reconcile 只读，不自动补 receipt。
- `task_dag.py`：Stage 2 后 DAG 派单、交叉复核、重规划、级联失效和写入域检查。
- `score_artifact.py`：Critic schema/评分重算、逐问聚合与持久化；CLI 不调用模型。
- `extract_diff.py`：章节补丁/统一差异应用，拒绝陈旧上下文。
- `render_paper.py`：编号 Markdown→三赛事模板→PDF；支持 Tectonic 与 `--no-compile`。
- `render_ai_usage.py`：按赛事从真实 AI 台账生成声明/报告。
- `pdf_audit.py`：赛事边界、缺字/占位、Overfull/Underfull、元数据/密度、逐页渲染与视觉复核 gate。
- `check_layout.py`：**advisory layout lint**；图表引用距离、图形密度、图挨图、caption 长度、目标页数。经验阈值默认只 hint/review，不冒充赛事硬规则。
- `citation_audit.py`：参考文献与正文引用一致性。
- `verify_independence.py`：防“独立复算”直接 import/重跑被验实现。
- `claim_registry.py`：headline/innovation claim 的 source、验证器与 SHA provenance。
- `final_gate.py`：最终统一 READY/BLOCKED。
- `prose_lint.py`：表达建议与数字/公式/引用/否定保护。
- `corpus.py`：本地论文去重、QA 与分组统计。
- `diagrams/check_overlap.py`：架构图 PDF 文字边界盒重叠/越界提示；规则见 `references/architecture-diagram.md`。
- `ingest_papers.py`、`download_cumcm_papers.py`：赛前维护工具，不自动覆盖当前项目证据。

求解脚本的数据路径策略不是“硬编码绝对路径”。推荐 `--workspace` / config / manifest + 项目相对路径；日志可记录解析后的绝对路径用于诊断。仓库状态、DAG、claim source 与论文引用不得依赖某个队员机器专属的 `C:\Users\...` 或 `/home/...`。

AI 台账保留工具、型号/版本（不可见则注明）、环节、用途、过程说明、采纳和核验记录。missing/null 不是未使用；不得伪造人工审查。
