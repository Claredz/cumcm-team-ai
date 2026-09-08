# 往届论文来源数据集与经验统计

本目录包含 2023、2024、2025 年官方展廊索引中发现的论文元数据 JSON：编号、年份、题型、标题、详情链接和来源页。它是检索学习的数据集，不声称包含完整获奖总体或这些论文的全文。索引按页面实际返回条目采集，分页/未列出的论文可能缺失；页面无内容必须如实记录。

全文来源为中国大学生在线官方展示页面；页面涉及的文字、图像和论文版权仍属原权利人。本公开仓库不将它们当 MIT 素材再分发。可在队内按实际使用权限取得论文后，用 scripts/corpus.py 导入到项目 local-corpus/。

另有 [国赛经验统计](../../competitions/cumcm/empirical.json) 和 [统计解释](../../competitions/cumcm/empirical_notes.md)：继承上游记录的 91 份来源 / 59 份可提取样本观察分位，并非本目录三年索引的统计结果，也不是本次独立复现。其历史逐篇原始数据未随上游发布，不能声称可由本包直接复建原值。美赛/电工杯 empirical 保留 n=0 的明确空基线。

新统计链支持本地 PDF 文本提取、内容哈希去重、扫描/乱码/来源缺失过滤、逐篇统计和按年/题型分组样本量。所有接受与排除记录留在 JSON 中，可复查为何某论文没有进入分位数；不给 n=0 的子集编造阈值。

```bash
python scripts/corpus.py discover --url https://dxs.moe.gov.cn/zx/hd/sxjm/sxjmlw/2024qgdxssxjmjslwzs/ --year 2024 --output /path/to/project/paper-index.json
python scripts/corpus.py ingest --papers-dir /path/to/project/local-corpus --manifest /path/to/project/sources.json --output /path/to/project/corpus.json
python scripts/corpus.py stats --index /path/to/project/corpus.json --output /path/to/project/statistics.json
```

导入 manifest 的每篇需提供 filename、year、topic、url、usage_basis。统计只能解释“这批可提取样本是什么样”，不能推出图表/篇幅决定奖项。
