[English](./README_EN.md)

# x-content-review

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3-green.svg)

X(Twitter) 账号数据内容复盘 skill。把账号数据变成可执行的运营决策:什么类别内容效率高、什么北京时间段发帖效果好、哪些帖子该扩成系列、哪些该换头重发、哪些选题该停。

## 功能

- **时段分析**:按北京时间 2 小时分桶,计算各时段转化效率(CSV 模式下发帖时间从 Post id 雪花 ID 反推,精确到秒)。
- **类别转化**:按关键词把帖子分类(关键词表可自定义),计算各类别转化效率,reply 单列。
- **单帖 A/B/C 分级**:A=高曝光高收藏(扩系列)、B=低曝光高收藏(换头重发)、C=双低(停选题)。
- **粉丝趋势**:pulse 模式每次运行自动记录粉丝数快照,积累后算周环比;CSV 模式直接有日度净涨粉。
- **复盘报告**:由 agent 基于分析 JSON 生成 Markdown 周报,附下周发帖指导。

## 数据源

| 模式 | 数据 | 说明 |
|---|---|---|
| Pulse(默认) | cookie 登录态拉最近帖子公开指标 + 粉丝数 | 零手工导出;口径为收藏/万曝光 |
| CSV(增强) | X Analytics 后台导出的 overview + content CSV | 含净涨粉、主页访问等后台独有数据,口径升级为涨粉/万曝光;有就自动用 |

## 使用

前置条件是 X cookie(`X_AUTH_TOKEN`/`X_CT0`),复制步骤见[仓库 README](../README.md#前置条件x-cookie一次配置全包通用)。作为 Claude Code / Codex skill 安装后,对 agent 说「X复盘」「出X周报」即可。

脚本也可独立运行:

```bash
pip3 install twscrape

# pulse 模式:拉数 → 分析
python3 scripts/fetch_x_pulse.py --user your_handle --limit 100 \
  --snapshot-file snapshots.jsonl > pulse.json
python3 scripts/analyze_x_data.py --pulse pulse.json --snapshots snapshots.jsonl --days 7

# CSV 模式
python3 scripts/analyze_x_data.py \
  --overview account_overview_analytics.csv \
  --content account_analytics_content.csv --days 7

# 主页信息(bio/头像/banner/置顶,供 x-account-audit 用)
python3 scripts/fetch_x_pulse.py --user your_handle --profile
```

## 安装(Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
ln -s "$(pwd)/x-operation-skills/x-content-review" ~/.claude/skills/x-content-review
```

## License

MIT
