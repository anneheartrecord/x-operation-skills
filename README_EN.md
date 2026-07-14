[中文](./README.md)

# x-operation-skills

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

A set of X (Twitter) operation skills for AI agents (Claude Code / Codex). Install them, configure your cookie once, then ask the agent in one sentence to review analytics, audit your account, post, or turn a hot topic into a tweet.

## What it does

| Skill | Purpose | Ask the agent |
|---|---|---|
| **x-content-review** | Pull your account data, find **which content and which time slots grow followers fastest**, give next-week guidance | "X weekly review" |
| **x-account-audit** | Audit bio / pinned / avatar / banner, hand back ready-to-use rewrites | "audit my X account" |
| **x-post** | Post via the official API with a cost preview and confirmation; auto-splits long form into a thread | "post this to X" |
| **x-hotspot-radar** | Scan hot topics → filter → draft a tweet in your voice, de-AI'd, with images | "what to post today" |

Also included: daily follower snapshot + **unattended weekly report** (launchd), benchmark tracking, topic-library loop, and cookie health check.

## How to use

**1. Configure the cookie (once, lasts months)** — log in to x.com, F12 → Application → Cookies → `x.com`, copy `auth_token` and `ct0` into `~/.config/secrets/api-keys.env`:

```bash
export X_AUTH_TOKEN="..."
export X_CT0="..."
export X_PROXY="http://127.0.0.1:7890"   # required where X is blocked
```

Then `pip3 install twscrape curl_cffi` (add `tweepy` for posting).

**2. Install the skills**

```bash
git clone https://github.com/anneheartrecord/x-operation-skills.git
for s in x-content-review x-account-audit x-post x-hotspot-radar; do
  ln -s "$(pwd)/x-operation-skills/$s" ~/.claude/skills/$s
done
```

**3. Use** — ask the agent "X weekly review" or "audit my X account". Reads use your cookie (free); posting uses the official pay-per-use API (text $0.015, with-link $0.20 — so x-post pools links into the thread's last tweet), always previewed before sending.

## Real sample (@Charles77xixi)

- **This week vs last**: 26 vs 21 posts, impressions −34%, but efficiency (bookmarks/10k views) 44.2 vs 45.1 — the drop is reach, not conversion.
- **Category efficiency**: 投资 39.7 > 开户 31.2 > 职业 26.7 > AI 工程 14.0 > 其他 6.9. Investing/brokerage convert best, yet AI-engineering is the 2nd most posted (68) at 35% of investing's efficiency — effort and conversion are inverted.
- **Best time slots** (UTC+8): 14–16 (67.4) and 20–22 (54.9) are prime, but the most posts land at 18–20 (54 posts, only 9.1).
- **Account audit**: the bio is an identity-stack + capability-list double anti-pattern; the skill returns 3 ready rewrites.

## Data & automation

Runtime data lives in `~/.local/share/x-operation-skills/` (contains login state, deliberately kept out of git). Optional launchd jobs record follower counts daily and produce the weekly report unattended; a cookie health check warns you to reconfigure when the cookie expires.

## Methodology

Account-audit framework from *Turning Talent into Money* (Wang Mengke) + Vista8's (@vista8) X growth methodology.

## License

MIT
