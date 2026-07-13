[中文](./README.md)

# x-operation-skills

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

A collection of X (Twitter) account operation skills. Each subdirectory is a standalone skill installable into Claude Code / Codex or any agent that supports SKILL.md.

## Skills

| Skill | Purpose | Trigger |
|---|---|---|
| [x-content-review](./x-content-review/) | Data review: posting time-slot conversion (UTC+8), category efficiency, A/B/C post grading, weekly report with next-week guidance | "X weekly review" |
| [x-account-audit](./x-account-audit/) | Profile audit: bio, pinned post, banner, avatar, recognizability, and profile funnel, with ready-to-use rewrites | "audit my X account" |

Planned: x-hotspot-radar (trending-topic radar: hot topic digest → tweet drafts).

## Prerequisite: X cookies (configure once, shared by all skills)

Both skills read data through your own account's login cookies by default (the official X API no longer has a free tier). One-time setup:

1. Log in to x.com in your browser.
2. Press F12 to open DevTools → **Application** tab (Chrome/Edge; **Storage** in Firefox) → **Cookies** → `https://x.com`.
3. Find the `auth_token` row and copy its **Value**; do the same for `ct0`.
4. Save them as environment variables (ideally in a private file such as `~/.config/secrets/api-keys.env`, sourced by your shell):

```bash
export X_AUTH_TOKEN="auth_token value from step 3"
export X_CT0="ct0 value from step 3"
```

5. Install the dependency: `pip3 install twscrape`.

Treat cookies like passwords: keep them in a local private file and never commit them. Logging out of x.com invalidates them; log back in and copy again.

Optional enhancement: x-content-review also consumes CSVs exported from the X Analytics dashboard (which contain net follows and profile visits, unavailable via cookies). If present, they are used automatically.

## Install (Claude Code)

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
ln -s "$(pwd)/x-operation-skills/x-content-review" ~/.claude/skills/x-content-review
ln -s "$(pwd)/x-operation-skills/x-account-audit" ~/.claude/skills/x-account-audit
```

## Methodology

- Data review: bookmarks-or-follows per 10k impressions, A/B/C post grading, posting time derived from Snowflake IDs.
- Account audit: based on the trust-and-monetization framework from *Turning Talent into Money* (Wang Mengke) and Vista8's (@vista8) X growth methodology.

## License

MIT
