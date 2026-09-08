# Windows 10/11 原生环境配置

本页面面向不使用 WSL 的队员。目标是让 Windows PowerShell 成为一等支持环境，而不是要求队员比赛前临时学习 Linux。

## 1. 支持范围

核心 workflow、DAG、claim/citation/PDF/layout 工具均使用 Python/`pathlib`/跨平台 subprocess 接口。正式支持目标：

- Windows 10/11 + PowerShell / Windows Terminal；
- Python 3.10+；
- Git for Windows；
- Pandoc；
- CUMCM/电工杯：XeLaTeX + `ctexart.cls`，推荐 TeX Live 或 MiKTeX；
- MCM/ICM：pdfLaTeX 或兼容引擎。

GitHub Actions 会在 `windows-latest` 上执行核心回归；TeX/Pandoc 完整安装仍由本机 `doctor.py` 检查。

## 2. 安装 skill

在项目根目录打开 PowerShell：

```powershell
New-Item -ItemType Directory -Force .agents\skills | Out-Null
git clone https://github.com/Claredz/cumcm-team-ai.git .agents\skills\cumcm-team-ai
python -m pip install -r .agents\skills\cumcm-team-ai\requirements.txt
```

若 `python` 命令不可用但 Python 已安装，可尝试 `py -3`；比赛前建议统一让 `python --version` 正常工作，避免队员之间命令不同。

### UTF-8 CLI 模式

AI harness、IDE 或测试框架经常通过 pipe 捕获 Python stdout/stderr。Windows 的非交互 pipe 可能回退到本地代码页，因此比赛环境应显式启用 Python UTF-8 模式，避免中文诊断输出触发 `UnicodeEncodeError`。

当前 PowerShell 会话：

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
```

若这台机器专门用于比赛并希望新终端自动继承，可写入当前用户环境后重新打开 PowerShell：

```powershell
[Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', 'User')
[Environment]::SetEnvironmentVariable('PYTHONIOENCODING', 'utf-8', 'User')
```

不想修改持久环境时，可对单次 Python 命令使用 `python -X utf8 ...`。GitHub Windows CI 同时设置 `PYTHONUTF8=1` 与 `PYTHONIOENCODING=utf-8`，用于覆盖真实的 agent/subprocess 捕获场景。

## 3. 安装外部工具

需要正式生成论文 PDF 时安装：

- Pandoc：安装后确认 `pandoc --version`；
- TeX Live 或 MiKTeX：确认 `xelatex --version`、`pdflatex --version`；
- CUMCM/电工杯额外确认 `kpsewhich ctexart.cls` 能返回路径。

安装后重新打开 PowerShell，让 PATH 与用户环境变量刷新。

## 4. 预检

从 skill 根目录或使用完整路径运行：

```powershell
python scripts\doctor.py --competition cumcm
python scripts\doctor.py --competition mcm
python scripts\doctor.py --competition diangong
```

只验证 Python 包结构与核心逻辑，不检查本地 TeX/Pandoc：

```powershell
python scripts\doctor.py --competition cumcm --skip-tools
```

正式比赛前应至少对所参加赛事跑一次不带 `--skip-tools` 的 doctor。

## 5. 项目初始化与 DAG

以下命令在 PowerShell 直接可用；路径有空格时用引号包住：

```powershell
python .agents\skills\cumcm-team-ai\scripts\workflow.py init --workspace . --competition cumcm --year 2026 --formal-contest
python .agents\skills\cumcm-team-ai\scripts\doctor.py --competition cumcm --workspace .
python .agents\skills\cumcm-team-ai\scripts\task_dag.py board --workspace .
```

核心命令不要求 Git Bash，也不依赖 `grep`、`sed`、`tee` 或 Bash process substitution。

## 6. 路径与三机协作

代码和状态只记录项目相对逻辑路径，例如：

```text
data/raw/附件1.xlsx
runs/Q2/final/result.json
paper_workspace/main.tex
```

不要把：

```text
C:\Users\Alice\Desktop\...
```

写进最终脚本或论文。运行日志可记录解析后的绝对路径用于诊断，但 artifact/DAG/manifest 应使用项目相对路径。这样同一仓库可由 Windows、WSL、Linux 队员共同使用。

## 7. PowerShell 与 Bash 示例

仓库中的权威执行入口以 Python CLI 为主。历史/导入参考中若出现 `grep`、`cp`、`tee`、反斜杠续行等 Bash 示例，只表示一种人工检查方式，不是 workflow 前置依赖。

PowerShell 常用等价命令：

```powershell
# cp
Copy-Item source.tex target.tex

# grep 文本定位
Select-String -Path main.tex -Pattern '0\.592|34\.91|3862'

# tee
python solve.py | Tee-Object -FilePath run.log
```

真正需要跨平台自动化时，优先使用仓库 Python 脚本，而不是把 shell 差异写入 DAG。

## 8. 比赛前 10 分钟验收

```powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts templates\shared\code_starter
python scripts\doctor.py --competition cumcm --require-modeling
```

如果正式论文用 XeLaTeX，再执行一次真实短稿编译和 `pdf_audit.py`。不要在比赛开始后才首次安装 TeX、修 PATH 或首次发现 Python pipe 编码问题。
