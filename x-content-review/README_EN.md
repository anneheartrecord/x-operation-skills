[中文](./README.md)

# x-content-review

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3-green.svg)

An agent skill that turns your X (Twitter) account data into actionable operating decisions: which content categories are most efficient, which posting time slots work best, which posts to expand into a series, which to repackage and repost, and which topics to drop.

## Features

- **Time-slot analysis**: 2-hour buckets in UTC+8 scored by conversion efficiency (in CSV mode, posting time is derived from the Post id Snowflake ID with second-level precision).
- **Category conversion**: keyword-based post classification (customizable keyword map) with per-category efficiency; replies tracked separately.
- **Post grading (A/B/C)**: A = high exposure + high bookmarks (expand into a series), B = low exposure + high bookmarks (repackage and repost), C = low on both (drop the topic).
- **Follower trend**: pulse mode appends a follower-count snapshot on every run, enabling week-over-week deltas; CSV mode has daily net follows natively.
- **Review report**: the agent writes a Markdown weekly report from the analysis JSON, ending with concrete next-week posting guidance.

## Data sources

| Mode | Data | Notes |
|---|---|---|
| Pulse (default) | recent public post metrics + follower count via login cookies | zero manual export; metric is bookmarks per 10k views |
| CSV (enhanced) | overview + content CSV exported from X Analytics | adds dashboard-only net follows and profile visits, upgrading the metric to follows per 10k impressions; used automatically when present |

## Usage

The prerequisite is a pair of X cookies (`X_AUTH_TOKEN`/`X_CT0`); see the [repo README](../README_EN.md#prerequisite-x-cookies-configure-once-shared-by-all-skills) for copy steps. Once installed as a Claude Code / Codex skill, ask the agent for an "X weekly review".

The scripts also run standalone:

```bash
pip3 install twscrape

# pulse mode: fetch, then analyze
python3 scripts/fetch_x_pulse.py --user your_handle --limit 100 \
  --snapshot-file snapshots.jsonl > pulse.json
python3 scripts/analyze_x_data.py --pulse pulse.json --snapshots snapshots.jsonl --days 7

# CSV mode
python3 scripts/analyze_x_data.py \
  --overview account_overview_analytics.csv \
  --content account_analytics_content.csv --days 7

# profile info (bio/avatar/banner/pinned, consumed by x-account-audit)
python3 scripts/fetch_x_pulse.py --user your_handle --profile
```

## Install (Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
ln -s "$(pwd)/x-operation-skills/x-content-review" ~/.claude/skills/x-content-review
```

## License

MIT
