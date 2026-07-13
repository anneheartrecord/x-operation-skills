#!/usr/bin/env python3
"""对标账号追踪:拉一批对标账号的公开数据,输出横向对比 + 各自最近高表现帖。

看对标在发什么、发多勤、什么帖成了(供选题和节奏参考)。数据都是公开指标
(views/likes/收藏),经 cookie 登录态 + 代理拉取,复用 fetch_x_pulse 的连接逻辑。

对标清单来源(二选一):
  --handles a,b,c              逗号分隔的 handle(不带 @)
  --config benchmarks.txt      每行一个 handle(# 开头为注释)

用法:
  python3 track_benchmarks.py --handles vista8,zarazhangrui --limit 40
  python3 track_benchmarks.py --config benchmarks.txt --limit 40
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone

from fetch_x_pulse import build_api

TZ_BEIJING = timezone(timedelta(hours=8))


async def track_one(username, limit, window_days):
    """拉单个对标账号:主页信息 + 近期原创帖的表现汇总。"""
    api = await build_api(username)
    user = await api.user_by_login(username)
    if not user:
        return {"username": username, "error": "拉取失败(账号不存在或 cookie 失效)"}

    window_start = (datetime.now(TZ_BEIJING) - timedelta(days=window_days)).date()
    posts, seen = [], set()
    async for tweet in api.user_tweets(user.id, limit=limit):
        author = getattr(tweet.user, "username", "") if tweet.user else ""
        if author.lower() != username.lower() or str(tweet.id) in seen:
            continue
        seen.add(str(tweet.id))
        posts.append({
            "posted_at": tweet.date.astimezone(TZ_BEIJING),
            "text": tweet.rawContent[:80],
            "views": tweet.viewCount or 0,
            "likes": tweet.likeCount or 0,
            "bookmarks": tweet.bookmarkedCount or 0,
            "url": tweet.url,
        })

    window_posts = [p for p in posts if p["posted_at"].date() >= window_start]
    total_views = sum(p["views"] for p in window_posts)
    sorted_views = sorted((p["views"] for p in window_posts)) or [0]
    top = sorted(window_posts, key=lambda p: -p["views"])[:3]
    return {
        "username": username,
        "display_name": user.displayname,
        "bio": user.rawDescription,
        "followers": user.followersCount,
        "following": user.friendsCount,
        "window_days": window_days,
        "posts_in_window": len(window_posts),
        "posts_per_day": round(len(window_posts) / window_days, 1),
        "median_views": sorted_views[len(sorted_views) // 2],
        "avg_views": round(total_views / len(window_posts)) if window_posts else 0,
        "top_posts": [{"views": p["views"], "bookmarks": p["bookmarks"],
                       "text": p["text"], "url": p["url"]} for p in top],
    }


def load_handles(args):
    """从 --handles 或 --config 解析对标 handle 列表。"""
    if args.handles:
        return [h.strip().lstrip("@") for h in args.handles.split(",") if h.strip()]
    if args.config:
        with open(args.config, encoding="utf-8") as config_file:
            return [line.strip().lstrip("@") for line in config_file
                    if line.strip() and not line.startswith("#")]
    print("错误:需提供 --handles 或 --config", file=sys.stderr)
    sys.exit(1)


async def track_all(handles, limit, window_days):
    """逐个追踪对标账号(串行,避免共用 cookie 触发限流)。"""
    results = []
    for handle in handles:
        results.append(await track_one(handle, limit, window_days))
    return results


def main():
    parser = argparse.ArgumentParser(description="对标账号追踪(公开指标横向对比)")
    parser.add_argument("--handles", help="逗号分隔的 handle,不带 @")
    parser.add_argument("--config", help="每行一个 handle 的文件(# 注释)")
    parser.add_argument("--limit", type=int, default=40, help="每个账号拉取帖数上限")
    parser.add_argument("--days", type=int, default=14, help="统计窗口天数(默认 14)")
    args = parser.parse_args()

    try:
        import twscrape  # noqa: F401
    except ImportError:
        print("错误:未安装 twscrape,先执行 pip3 install twscrape curl_cffi", file=sys.stderr)
        sys.exit(1)

    handles = load_handles(args)
    results = asyncio.run(track_all(handles, args.limit, args.days))
    print(json.dumps({"generated_at": datetime.now(TZ_BEIJING).strftime("%Y-%m-%d %H:%M"),
                      "window_days": args.days, "benchmarks": results},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
