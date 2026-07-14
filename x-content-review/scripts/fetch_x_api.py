#!/usr/bin/env python3
"""X 官方 API 拉数(api 模式):按量计费读自己账号的数据,输出与 pulse 模式同构的 JSON。

计费(2026-07 官方 pay-per-use 口径):读自己的帖/粉丝/书签 $0.001/请求,
一次复盘通常 2-3 个请求,成本不到 1 美分。

依赖 tweepy(pip install tweepy),鉴权用 OAuth 1.0a user context,
四个环境变量(X 开发者后台 Keys and tokens 页生成,按惯例存
~/.config/secrets/api-keys.env):
  X_API_KEY / X_API_SECRET               -- Consumer Keys
  X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET -- 自己账号的 Access Token(读写权限)

相比 cookie pulse 模式的优势:官方接口稳定,且 public_metrics 含
impression_count(真曝光数),口径能对齐 analytics 后台。

用法:
  python3 fetch_x_api.py [--limit 100] [--snapshot-file 快照.jsonl]
"""

import argparse
import json
import os
import sys

from fetch_x_pulse import append_follower_snapshot

REQUIRED_ENV_KEYS = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]


def missing_credentials(env=None):
    """返回缺失的 OAuth 环境变量列表(纯函数,便于单测)。"""
    source = env if env is not None else os.environ
    return [key for key in REQUIRED_ENV_KEYS if not source.get(key)]


def build_client():
    """校验四个 OAuth 环境变量并构造 tweepy Client。"""
    import tweepy

    missing_keys = missing_credentials()
    if missing_keys:
        print(f"错误:缺少环境变量 {', '.join(missing_keys)}。\n"
              "到 developer.x.com 的项目 Keys and tokens 页生成 Consumer Keys 和\n"
              "Access Token(勾选 Read and write),存入 ~/.config/secrets/api-keys.env",
              file=sys.stderr)
        sys.exit(1)
    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def check_credentials():
    """凭证自检,返回 (ok, 说明)。缺变量→提示配置;鉴权失败→提示重新生成 token。"""
    missing_keys = missing_credentials()
    if missing_keys:
        return False, (f"缺少环境变量 {', '.join(missing_keys)}。到 developer.x.com "
                       "生成 Consumer Keys + Access Token(Read and write)存入 api-keys.env。")
    try:
        client = build_client()
        me = client.get_me(user_fields=["public_metrics"]).data
    except Exception as error:  # 鉴权/网络异常
        return False, (f"凭证鉴权失败:{type(error).__name__}: {error}。"
                       "检查 token 是否过期或权限是否为 Read and write。")
    return True, f"官方 API 凭证有效,@{me.username}。"


def fetch_own_posts(limit):
    """读自己账号最近的帖子与粉丝数,输出与 fetch_x_pulse.py 同构的 dict。"""
    client = build_client()
    me = client.get_me(user_fields=["public_metrics"]).data
    followers = me.public_metrics["followers_count"]

    posts = []
    pagination_token = None
    # 每页最多 100 条;每页一个请求($0.001),按 limit 分页
    while len(posts) < limit:
        page_size = min(100, max(5, limit - len(posts)))
        response = client.get_users_tweets(
            me.id, max_results=page_size, pagination_token=pagination_token,
            tweet_fields=["created_at", "public_metrics", "text"],
        )
        for tweet in (response.data or []):
            metrics = tweet.public_metrics
            posts.append({
                "id": str(tweet.id),
                "posted_at": tweet.created_at.isoformat(),
                "text": tweet.text[:80],
                "views": metrics.get("impression_count", 0),
                "likes": metrics.get("like_count", 0),
                "reposts": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "bookmarks": metrics.get("bookmark_count", 0),
                "url": f"https://x.com/{me.username}/status/{tweet.id}",
            })
        pagination_token = (response.meta or {}).get("next_token")
        if not pagination_token:
            break
    return {"user": me.username, "followers": followers, "posts": posts}


def main():
    parser = argparse.ArgumentParser(description="X 官方 API 拉自己账号数据(按量计费)")
    parser.add_argument("--limit", type=int, default=100, help="拉取帖子数上限(默认 100)")
    parser.add_argument("--snapshot-file", help="粉丝数快照 JSONL 路径(可选,用于算周环比涨粉)")
    parser.add_argument("--check", action="store_true",
                        help="凭证自检:有效退出 0,缺变量/鉴权失败退出 1 并给可操作提示")
    args = parser.parse_args()

    try:
        import tweepy  # noqa: F401
    except ImportError:
        print("错误:未安装 tweepy,先执行 pip3 install tweepy", file=sys.stderr)
        sys.exit(1)

    if args.check:
        ok, message = check_credentials()
        print(("OK: " if ok else "FAIL: ") + message, file=sys.stderr)
        sys.exit(0 if ok else 1)

    result = fetch_own_posts(args.limit)
    if args.snapshot_file:
        append_follower_snapshot(args.snapshot_file, result["followers"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
