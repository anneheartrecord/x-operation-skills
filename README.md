[English](./README_EN.md)

# x-content-review

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3-green.svg)

X(Twitter) 账号数据内容复盘 skill。把 X Analytics 导出的 CSV 变成可执行的运营决策:什么类别涨粉快、什么北京时间段发帖效率高、哪些帖子该扩成系列、哪些该换头重发、哪些选题该停。

## 功能

- **周度趋势**:曝光、净涨粉、发帖数按周聚合,窗口汇总与环比。
- **时段分析**:发帖时间从 Post id(Snowflake ID)反推,精确到秒,按北京时间 2 小时分桶,计算各时段「涨粉/万曝光」。
- **类别转化**:按关键词把帖子分类(关键词表可自定义),计算各类别涨粉效率,reply 单列。
- **单帖 A/B/C 分级**:A=高曝光高收藏(扩系列)、B=低曝光高收藏(换头重发)、C=双低(停选题)。
- **复盘报告**:由 agent 基于分析 JSON 生成 Markdown 周报,附下周发帖指导。

## 数据源

| 模式 | 数据 | 说明 |
|---|---|---|
| CSV(默认、权威) | X Analytics 后台导出的 overview + content CSV | 含净涨粉、主页访问等后台独有数据 |
| Pulse(可选) | cookie 登录态拉最近帖子公开指标 | 依赖 twscrape,只有 views/likes/收藏,速览用 |

## 使用

作为 Claude Code / Codex skill 安装后,对 agent 说「X复盘」「出X周报」即可。

脚本也可独立运行:

```bash
python3 scripts/analyze_x_data.py \
  --overview account_overview_analytics.csv \
  --content account_analytics_content.csv \
  --days 7
```

Pulse 模式需要环境变量 `X_AUTH_TOKEN` 和 `X_CT0`(浏览器 x.com cookie 中复制),建议存放于 `~/.config/secrets/api-keys.env`。cookie 等同账号密码,不要写入仓库。

```bash
pip3 install twscrape
python3 scripts/fetch_x_pulse.py --user your_handle --limit 50
```

## 安装(Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-content-review.git
ln -s "$(pwd)/x-content-review" ~/.claude/skills/x-content-review
```

## License

MIT
