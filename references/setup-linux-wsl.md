# Linux / WSL2 环境配置

本页面适用于原生 Linux 和 Windows 上的 WSL2。对于已经熟悉 WSL 的队员，推荐把 Python、Git、Pandoc、TeX 与项目工作区都放在同一 WSL 发行版里，减少跨文件系统路径问题。

## 1. 支持范围

正式支持目标：

- Ubuntu/Linux；
- WSL2 + Ubuntu 等常见发行版；
- Python 3.10+；
- Git；
- Pandoc；
- CUMCM/电工杯：XeLaTeX + `ctexart.cls`；
- MCM/ICM：pdfLaTeX 或兼容引擎。

GitHub Actions 在 `ubuntu-latest` 上执行核心回归。WSL 运行时 `doctor.py` 会显示 WSL/Linux 平台标签。

## 2. 推荐工作区位置

WSL 下优先把比赛项目放在 Linux 文件系统，例如：

```text
~/cumcm/2026/
```

而不是长期在 `/mnt/c/...` 上运行大量 Python、Git 和 TeX 文件操作。Windows 应用需要访问时，可以通过资源管理器的 `\\wsl$\...` 入口查看。

这不是硬规则；核心原则是同一轮运行尽量不要让一个脚本同时混用 `C:\...` 和 `/mnt/c/...` 两套路径表示。

## 3. 安装 skill

```bash
mkdir -p .agents/skills
git clone https://github.com/Claredz/cumcm-team-ai.git .agents/skills/cumcm-team-ai
python -m pip install -r .agents/skills/cumcm-team-ai/requirements.txt
```

## 4. 安装外部工具

Ubuntu/WSL 的具体包名随发行版变化。安装完成后至少确认：

```bash
python --version
git --version
pandoc --version
xelatex --version
pdflatex --version
kpsewhich ctexart.cls
```

如果只做结构预览，可暂时没有 Pandoc/TeX；正式论文编译前必须补齐。

## 5. 预检

```bash
python scripts/doctor.py --competition cumcm
python scripts/doctor.py --competition mcm
python scripts/doctor.py --competition diangong
```

核心逻辑预检：

```bash
python scripts/doctor.py --competition cumcm --skip-tools
```

正式比赛前应对目标赛事至少跑一次完整 doctor。

## 6. 项目初始化与 DAG

```bash
python .agents/skills/cumcm-team-ai/scripts/workflow.py init --workspace . --competition cumcm --year 2026 --formal-contest
python .agents/skills/cumcm-team-ai/scripts/doctor.py --competition cumcm --workspace .
python .agents/skills/cumcm-team-ai/scripts/task_dag.py board --workspace .
```

DAG、receipt、claim registry 和论文状态中的 artifact 路径使用项目相对路径，不记录某一台机器专属的 `/home/<name>/...`。

## 7. 与 Windows 队员协作

共享仓库中的逻辑路径统一使用：

```text
data/raw/附件1.xlsx
runs/Q1/final/result.json
paper_workspace/main.tex
```

Python 用 `pathlib.Path` 解析，不手工拼接 `/` 或 `\\`。Windows 队员可以在本机把同一逻辑路径解析到 `D:\...`；WSL 队员解析到 `/home/...`，DAG 和论文引用保持一致。

如果要把 WSL 生成的最终 PDF 发给 Windows 队员，复制成普通 artifact 即可；不要让另一人的求解脚本依赖你的 `/home/...` 路径。

## 8. 比赛前验收

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts templates/shared/code_starter
python scripts/doctor.py --competition cumcm --require-modeling
```

再做一次真实短稿的 XeLaTeX 编译、`pdf_audit.py` 和视觉检查。比赛环境应在赛前冻结，不在比赛中无必要地升级 Python、TeX 或核心依赖。
