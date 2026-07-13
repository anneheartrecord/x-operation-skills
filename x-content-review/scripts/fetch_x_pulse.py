#!/usr/bin/env python3
"""X 账号快速拉数(pulse 模式):用登录 cookie 拉最近原创帖的公开指标或账号主页信息。

依赖 twscrape + curl_cffi(pip install twscrape curl_cffi),登录态来自环境变量:
  X_AUTH_TOKEN  -- x.com cookie 中的 auth_token
  X_CT0         -- x.com cookie 中的 ct0
  X_PROXY       -- (可选)访问 X 的代理,如 http://127.0.0.1:7890;
                   不设则退回 HTTPS_PROXY/HTTP_PROXY。国内访问 X 必须有代理。
前三者按惯例存放于 ~/.config/secrets/api-keys.env,由 shell 自动注入。

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


def resolve_proxy():
    """解析代理地址(国内访问 X 必需):优先 X_PROXY,退回 HTTPS_PROXY/HTTP_PROXY。"""
    return (os.environ.get("X_PROXY") or os.environ.get("HTTPS_PROXY")
            or os.environ.get("HTTP_PROXY") or None)


def patch_xclid_proxy(proxy):
    """把代理注入 twscrape 的 XClIdGen client(它自身不传 proxy,国内会连不上)。

    XClIdGen 生成 x-client-transaction-id 时新建的 httpx client 不带代理,且其自定义
    transport 会忽略 env 代理;这里强制它走 curl 后端并带上代理,是国内跑通的关键。
    """
    if not proxy:
        return
    import twscrape.xclid as xclid
    from twscrape.http import make_client

    def make_client_with_proxy(*_args, **kwargs):
        allowed = {key: kwargs[key] for key in ("headers", "cookies") if key in kwargs}
        return make_client("curl", proxy=proxy, **allowed)

    xclid._make_http_client = make_client_with_proxy


async def build_api(username):
    """校验 cookie 环境变量,构造并激活注入了单账号登录态的 twscrape API(代理感知)。"""
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

    proxy = resolve_proxy()
    patch_xclid_proxy(proxy)
    api = API(proxy=proxy)
    cookie_string = f"auth_token={auth_token}; ct0={ct0}"
    # twscrape 以「账号池」组织登录态;注入单个 cookie 账号(已存在则忽略),再标记 active
    try:
        await api.pool.add_account(username, "-", "-", "-",
                                   cookies=cookie_string, proxy=proxy)
    except Exception:  # 账号已存在等非致命情况,继续用池里的
        pass
    await api.pool.set_active(username, True)
    return api


async def fetch_profile(username):
    """拉取账号主页信息:bio、头像、banner、置顶帖、关注结构。供账号诊断用。"""
    api = await build_api(username)

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
    api = await build_api(username)

    user = await api.user_by_login(username)
    posts = []
    seen_ids = set()  # 分页偶尔返回重复帖,按 id 去重
    async for tweet in api.user_tweets(user.id, limit=limit):
        # 只保留作者是本人的帖。user_tweets 会混入转推(此 twscrape 版本不设
        # retweetedTweet,而是直接返回原作者的 tweet 对象),转推的曝光/收藏属于原
        # 作者,算进来会把百万曝光的官方号内容误计为本账号表现,彻底污染分析。
        tweet_author = getattr(tweet.user, "username", "") if tweet.user else ""
        if tweet_author.lower() != username.lower():
            continue
        if str(tweet.id) in seen_ids:
            continue
        seen_ids.add(str(tweet.id))
        posts.append({
            "id": str(tweet.id),
            "posted_at": tweet.date.isoformat(),
            "text": tweet.rawContent[:80],
            "views": tweet.viewCount,
            "likes": tweet.likeCount,
            "reposts": tweet.retweetCount,
            "replies": tweet.replyCount,
            "bookmarks": tweet.bookmarkedCount,
            # 标记引用推:引用是本账号的原创评论,保留但单独可辨
            "is_quote": getattr(tweet, "quotedTweet", None) is not None,
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
