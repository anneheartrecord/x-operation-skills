#!/usr/bin/env python3
"""X 账号快速拉数(pulse 模式):不导 CSV 时,用登录 cookie 拉最近原创帖的公开指标。

依赖 twscrape(pip install twscrape),登录态来自环境变量:
  X_AUTH_TOKEN  -- x.com cookie 中的 auth_token
  X_CT0         -- x.com cookie 中的 ct0
两者按惯例存放于 ~/.config/secrets/api-keys.env,由 shell 自动注入。

只能拿公开指标(views/likes/RT/bookmarks/回复数),拿不到 analytics 后台的
「净涨粉」「profile visits」——那些仍以 CSV 为准。

用法:
  python3 fetch_x_pulse.py --user Charles77xixi [--limit 50]
"""

import argparse
import asyncio
import json
import os
import sys


async def fetch_recent_posts(username, limit):
    """用 cookie 登录态拉取指定用户最近的帖子,返回公开指标列表。"""
    from twscrape import API

    auth_token = os.environ.get("X_AUTH_TOKEN", "")
    ct0 = os.environ.get("X_CT0", "")
    if not auth_token or not ct0:
        print("错误:缺少 X_AUTH_TOKEN / X_CT0 环境变量。"
              "从浏览器 x.com 的 cookie 里复制后存入 ~/.config/secrets/api-keys.env",
              file=sys.stderr)
        sys.exit(1)

    api = API()
    cookie_string = f"auth_token={auth_token}; ct0={ct0}"
    # twscrape 以「账号池」组织登录态;这里注入单个 cookie 账号
    await api.pool.add_account(username, "-", "-", "-", cookies=cookie_string)

    user = await api.user_by_login(username)
    posts = []
    async for tweet in api.user_tweets(user.id, limit=limit):
        posts.append({
            "id": str(tweet.id),
            "posted_at": tweet.date.isoformat(),
            "text": tweet.rawContent[:80],
            "views": tweet.viewCount,
            "likes": tweet.likeCount,
            "reposts": tweet.retweetCount,
            "replies": tweet.replyCount,
            "bookmarks": tweet.bookmarkedCount,
            "url": tweet.url,
        })
    return {"user": username, "followers": user.followersCount, "posts": posts}


def main():
    parser = argparse.ArgumentParser(description="X 账号 pulse 快速拉数(cookie 登录态)")
    parser.add_argument("--user", required=True, help="X 用户名(不带 @)")
    parser.add_argument("--limit", type=int, default=50, help="拉取帖子数上限(默认 50)")
    args = parser.parse_args()

    try:
        import twscrape  # noqa: F401
    except ImportError:
        print("错误:未安装 twscrape,先执行 pip3 install twscrape", file=sys.stderr)
        sys.exit(1)

    result = asyncio.run(fetch_recent_posts(args.user, args.limit))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
