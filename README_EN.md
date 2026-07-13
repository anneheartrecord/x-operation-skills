[中文](./README.md)

# x-operation-skills

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

A collection of X (Twitter) account operation skills. Each subdirectory is a standalone skill installable into Claude Code / Codex or any agent that supports SKILL.md.

## Skills

| Skill | Purpose | Trigger |
|---|---|---|
| [x-content-review](./x-content-review/) | Data review: weekly trends, posting time-slot conversion (UTC+8), category follower-efficiency, A/B/C post grading, weekly report with next-week guidance | "X weekly review" |
| [x-account-audit](./x-account-audit/) | Profile audit: bio, pinned post, banner, avatar, recognizability, and profile funnel, with ready-to-use rewrites | "audit my X account" |

Planned: x-hotspot-radar (trending-topic radar: hot topic digest → tweet drafts).

## Install (Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
ln -s "$(pwd)/x-operation-skills/x-content-review" ~/.claude/skills/x-content-review
ln -s "$(pwd)/x-operation-skills/x-account-audit" ~/.claude/skills/x-account-audit
```

## Methodology

- Data review: follows-per-10k-impressions conversion, A/B/C post grading, posting time derived from Snowflake IDs.
- Account audit: based on the trust-and-monetization framework from *Turning Talent into Money* (Wang Mengke) and Vista8's X growth methodology.

## License

MIT
