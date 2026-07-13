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
| [x-post](./x-post/) | Posting via the official X API: dry-run preview with cost estimate first, publishes only after explicit confirmation; supports replies and threads | "post this to X" |
| [x-hotspot-radar](./x-hotspot-radar/) | Hotspot radar: scan → five-filter → outline → calibration → draft → de-AI → images → save; orchestrates your existing writing/de-AI/image systems | "scan hotspots", "what to post today" |

## Credentials

### Official API (recommended: read your own data + post)

The official X API uses prepaid credits, deducted per request, no subscriptions. Key prices: reading your own posts/followers/bookmarks $0.001/request (a full review costs under a cent), posting a text tweet $0.015, posting a tweet with a link $0.20 (X deliberately suppresses external links).

1. Create a project at developer.x.com and purchase credits.
2. On the project's Keys and tokens page, generate Consumer Keys and an Access Token (check **Read and write**).
3. Save the four values as environment variables (ideally `~/.config/secrets/api-keys.env`):

```bash
export X_API_KEY="..."
export X_API_SECRET="..."
export X_ACCESS_TOKEN="..."
export X_ACCESS_TOKEN_SECRET="..."
```

4. Install the dependency: `pip3 install tweepy`.

### Cookies (free fallback: read-only)

Without prepaid credits, x-content-review and x-account-audit can still read data via login cookies (x-post requires the official API; cookies cannot write):

1. Log in to x.com in your browser.
2. Press F12 to open DevTools → **Application** tab (Chrome/Edge; **Storage** in Firefox) → **Cookies** → `https://x.com`.
3. Find the `auth_token` row and copy its **Value**; do the same for `ct0`.
4. Save them as environment variables (ideally in a private file such as `~/.config/secrets/api-keys.env`, sourced by your shell):

```bash
export X_AUTH_TOKEN="auth_token value from step 3"
export X_CT0="ct0 value from step 3"
```

5. Install dependencies: `pip3 install twscrape curl_cffi` (curl_cffi is required for TLS fingerprint impersonation; without it, cookie reads fail on some networks).
6. If X is blocked on your network, set `export X_PROXY="http://127.0.0.1:7890"` (your proxy port); the scripts fall back to `HTTPS_PROXY`/`HTTP_PROXY` if unset.

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
