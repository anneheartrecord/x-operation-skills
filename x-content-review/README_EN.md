[中文](./README.md)

# x-content-review

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3-green.svg)

An agent skill that turns X (Twitter) Analytics exports into actionable operating decisions: which content categories convert followers fastest, which posting time slots are most efficient, which posts to expand into a series, which to repackage and repost, and which topics to drop.

## Features

- **Weekly trends**: impressions, net follower growth, and post count aggregated by week, with window summary.
- **Time-slot analysis**: posting time is derived from the Post id (Snowflake ID) with second-level precision, bucketed into 2-hour slots (UTC+8), scoring each slot by "follows per 10k impressions".
- **Category conversion**: keyword-based post classification (customizable keyword map) with follower-efficiency per category; replies tracked separately.
- **Post grading (A/B/C)**: A = high exposure + high bookmarks (expand into a series), B = low exposure + high bookmarks (repackage and repost), C = low on both (drop the topic).
- **Review report**: the agent writes a Markdown weekly report from the analysis JSON, ending with concrete next-week posting guidance.

## Data sources

| Mode | Data | Notes |
|---|---|---|
| CSV (default, authoritative) | overview + content CSV exported from X Analytics | includes net follows and profile visits, which are dashboard-only |
| Pulse (optional) | recent public post metrics fetched via login cookies | requires twscrape; views/likes/bookmarks only, for a quick glance |

## Usage

Once installed as a Claude Code / Codex skill, ask the agent for an "X weekly review".

The scripts also run standalone:

```bash
python3 scripts/analyze_x_data.py \
  --overview account_overview_analytics.csv \
  --content account_analytics_content.csv \
  --days 7
```

Pulse mode requires the `X_AUTH_TOKEN` and `X_CT0` environment variables (copied from x.com browser cookies). Treat cookies like passwords; never commit them.

```bash
pip3 install twscrape
python3 scripts/fetch_x_pulse.py --user your_handle --limit 50
```

## Install (Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
ln -s "$(pwd)/x-operation-skills/x-content-review" ~/.claude/skills/x-content-review
```

## License

MIT
