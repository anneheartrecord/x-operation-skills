#!/usr/bin/env python3
"""X 账号快速拉数(pulse 模式):用登录 cookie 拉最近原创帖的公开指标或账号主页信息。

依赖 twscrape(pip install twscrape),登录态来自环境变量:
  X_AUTH_TOKEN  -- x.com cookie 中的 auth_token
  X_CT0         -- x.com cookie 中的 ct0
两者按惯例存放于 ~/.config/secrets/api-keys.env,由 shell 自动注入。

只能拿公开指标(views/likes/RT/bookmarks/回复数),拿不到 analytics 后台的
「净涨粉」「profile visits」——那些以 X Analytics 导出的 CSV 为准。

用法:
  python3 fetch_x_pulse.py --user Charles77xixi [--limit 50] [--snapshot-file 快照.jsonl]
  python3 fetch_x_pulse.py --user Charles77xixi --profile   # 只拉主页信息(bio/头像/banner/置顶)

--snapshot-file 把 {date, followers} 追加进 JSONL(同日去重),积累后可算周环比涨粉。
"""

import argparse
import asyncio
import json
import os
import sys


def build_api(username):
    """校验 cookie 环境变量并构造注入了单账号登录态的 twscrape API。"""
    from twscrape import API

    auth_token = os.environ.get("X_AUTH_TOKEN", "")
    ct0 = os.environ.get("X_CT0", "")
    if not auth_token or not ct0:
        print("错误:缺少 X_AUTH_TOKEN / X_CT0 环境变量。\n"
              "获取方法:浏览器登录 x.com → F12 → Application → Cookies → x.com,\n"
              "复制 auth_token 和 ct0 两项的 Value,存入 ~/.config/secrets/api-keys.env:\n"
              '  export X_AUTH_TOKEN="..."\n  export X_CT0="..."',
              file=sys.stderr)
        sys.exit(1)
    api = API()
    cookie_string = f"auth_token={auth_token}; ct0={ct0}"
    # twscrape 以「账号池」组织登录态;这里注入单个 cookie 账号
    return api, api.pool.add_account(username, "-", "-", "-", cookies=cookie_string)


async def fetch_profile(username):
    """拉取账号主页信息:bio、头像、banner、置顶帖、关注结构。供账号诊断用。"""
    api, add_account_coro = build_api(username)
    await add_account_coro

    user = await api.user_by_login(username)
    pinned_posts = []
    for pinned_id in (user.pinnedIds or []):
        pinned_tweet = await api.tweet_details(int(pinned_id))
        if pinned_tweet:
            pinned_posts.append({"id": str(pinned_tweet.id),
                                 "text": pinned_tweet.rawContent,
                                 "views": pinned_tweet.viewCount,
                                 "likes": pinned_tweet.likeCount,
                                 "bookmarks": pinned_tweet.bookmarkedCount})
    return {
        "username": user.username,
        "display_name": user.displayname,
        "bio": user.rawDescription,
        "location": user.location,
        "bio_links": [link.url for link in (user.descriptionLinks or [])],
        "avatar_url": user.profileImageUrl,
        "banner_url": user.profileBannerUrl,
        "followers": user.followersCount,
        "following": user.friendsCount,
        "pinned_posts": pinned_posts,
    }


async def fetch_recent_posts(username, limit):
    """用 cookie 登录态拉取指定用户最近的帖子,返回公开指标列表。"""
    api, add_account_coro = build_api(username)
    await add_account_coro

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


def append_follower_snapshot(snapshot_path, followers):
    """把当日粉丝数快照追加到 JSONL(同一天已有记录则覆盖为最新值)。"""
    from datetime import date
    today = date.today().isoformat()
    existing_lines = []
    if os.path.exists(snapshot_path):
        with open(snapshot_path, encoding="utf-8") as snapshot_file:
            existing_lines = [json.loads(line) for line in snapshot_file if line.strip()]
    existing_lines = [record for record in existing_lines if record.get("date") != today]
    existing_lines.append({"date": today, "followers": followers})
    with open(snapshot_path, "w", encoding="utf-8") as snapshot_file:
        for record in existing_lines:
            snapshot_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="X 账号 pulse 快速拉数(cookie 登录态)")
    parser.add_argument("--user", required=True, help="X 用户名(不带 @)")
    parser.add_argument("--limit", type=int, default=50, help="拉取帖子数上限(默认 50)")
    parser.add_argument("--snapshot-file", help="粉丝数快照 JSONL 路径(可选,用于算周环比涨粉)")
    parser.add_argument("--profile", action="store_true",
                        help="只拉主页信息(bio/头像/banner/置顶帖),供账号诊断用")
    args = parser.parse_args()

    try:
        import twscrape  # noqa: F401
    except ImportError:
        print("错误:未安装 twscrape,先执行 pip3 install twscrape", file=sys.stderr)
        sys.exit(1)

    if args.profile:
        result = asyncio.run(fetch_profile(args.user))
    else:
        result = asyncio.run(fetch_recent_posts(args.user, args.limit))
        if args.snapshot_file:
            append_follower_snapshot(args.snapshot_file, result["followers"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
