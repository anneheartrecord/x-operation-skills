[中文](./README.md)

# x-hotspot-radar

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Language](https://img.shields.io/badge/Language-Python3%20%2B%20Markdown-green.svg)

An X (Twitter) hotspot radar skill: turn "what's worth riding today" into a tweet draft that matches your voice, has AI-flavor removed, comes with images, and is ready to publish.

## Role: orchestration, not reinvention

This skill does three things only: **hotspot scanning + five-filter screening + pipeline wiring**. Voice, de-AI, imagery, and publishing all call systems you already have installed:

| Stage | Calls |
|---|---|
| Voice | your writing-style system + anchor samples |
| Opening / pre-publish diagnosis | `dbs-hook`, `dbs-resonate` |
| De-AI | `de-ai-flavor` |
| Images / cover | `ian-xiaohei-illustrations`, `guizang-material-illustration`, `cover-image` |
| Publish | sibling `x-post` (dry-run + confirmation) |

## Flow

1. Scan (`scripts/scan_hotspots.py` builds a query plan; the agent runs WebSearch/WebFetch).
2. Five filters: relevance / unique angle / timeliness / trust gain / sustainability — fail any, drop it.
3. Propose angles and outline, wait for approval (mandatory step).
4. Write the opening for style calibration, wait for feedback.
5. Draft the full piece.
6. De-AI via `de-ai-flavor`.
7. Images (optional).
8. Save the draft to the tweets directory; stop here by default.
9. Publish only on explicit request, via `x-post`.

## License

MIT
