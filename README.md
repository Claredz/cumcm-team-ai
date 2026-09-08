# CUMCM Team AI

支持全国大学生数学建模竞赛的备赛与三人 AI 辅助协作 skill。

## 功能特点

- **三人协作**：A（模型与决策）、B（数据与求解）、C（论证与交付）
- **72 小时排期**：详细的 72 小时完成方案及休息安排
- **规则核查**：2026 年竞赛规则快照及官方来源
- **验证方法**：不同题型的有效核验和代码—论文证据链
- **学习资源**：论文、教材、经验链接及分工学习安排

## 目录结构

```
├── skills/cumcm-team-ai/          # 主 skill 目录
│   ├── SKILL.md                   # 主文件
│   ├── references/                # 参考文档
│   │   ├── rules-2026.md          # 规则快照
│   │   ├── schedule.md            # 72 小时排期
│   │   ├── team-workflow.md       # 三人协作
│   │   ├── verification.md        # 验证方法
│   │   └── learning-resources.md  # 学习资源
│   ├── assets/                    # 模板文件
│   │   ├── team-state.json        # 队伍状态
│   │   ├── task-card.md           # 任务卡
│   │   └── ai-usage-record.md     # AI 使用记录
│   └── agents/                    # 代理配置
│       └── openai.yaml            # OpenAI 配置
├── research/                      # 调研资料
│   ├── 2026国赛调研与skills对比.md
│   ├── skill-validation.md
│   └── sources/                   # 参考来源
├── .agents/                       # 代理配置
└── .gitignore                     # Git 忽略文件
```

## 使用方法

1. **备赛阶段**：阅读 `learning-resources.md`，按计划学习
2. **比赛阶段**：按照 `schedule.md` 推进，使用 `task-card.md` 跟踪任务
3. **验证阶段**：按照 `verification.md` 进行代码—论文验证

## 官方规则

- **比赛时间**：2026-09-10 18:00 至 09-13 20:00（共 74 小时）
- **MD5 提交**：09-13 20:00 前提交最终文件 MD5
- **文件上传**：09-13 20:30 至 09-14 14:00 上传对应文件

## 相关链接

- [国赛官网](https://www.mcm.edu.cn/)
- [2026 第一次通知](https://www.mcm.edu.cn/html_cn/node/d6fd7a0ee8f3a3d525e30af1c365fcec.html)
- [AI 工具使用规定](https://www.mcm.edu.cn/html_cn/node/fef94648f2836ab6cc81586f4c38512b.html)

## 许可证

MIT License