#!/usr/bin/env python3
"""通过 X 官方 API 发帖(按量计费:纯文字 $0.015/条,含链接 $0.20/条)。

鉴权与 fetch_x_api.py 相同,OAuth 1.0a user context,四个环境变量:
  X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET

安全设计:
  - 必须带 --yes 才真正发布,否则只做 dry-run 预览(打印内容与预估费用)
  - 检测到正文含链接时,dry-run 会明确提示 13 倍溢价($0.20)

用法:
  python3 post_tweet.py --text "内容"                 # dry-run 预览
  python3 post_tweet.py --text "内容" --yes           # 真正发布
  python3 post_tweet.py --text "内容" --reply-to <id> --yes   # 回复某条帖
"""

import argparse
import json
import os
import re
import sys

REQUIRED_ENV_KEYS = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
URL_PATTERN = re.compile(r"https?://\S+|(?:^|\s)\w[\w.-]*\.(?:com|cn|io|ai|net|org|dev)(?:/\S*)?",
                         re.IGNORECASE)


def estimate_cost(text):
    """按官方计费口径预估这条帖的费用:含链接 $0.20,纯文字 $0.015。"""
    has_url = bool(URL_PATTERN.search(text))
    return ("$0.20(含链接,13 倍溢价)" if has_url else "$0.015(纯文字)"), has_url


def build_client():
    """校验四个 OAuth 环境变量并构造 tweepy Client。"""
    import tweepy

    missing_keys = [key for key in REQUIRED_ENV_KEYS if not os.environ.get(key)]
    if missing_keys:
        print(f"错误:缺少环境变量 {', '.join(missing_keys)}。\n"
              "到 developer.x.com 生成 Consumer Keys 和 Access Token(Read and write),\n"
              "存入 ~/.config/secrets/api-keys.env",
              file=sys.stderr)
        sys.exit(1)
    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def main():
    parser = argparse.ArgumentParser(description="X 官方 API 发帖(默认 dry-run,--yes 才发布)")
    parser.add_argument("--text", required=True, help="帖子正文")
    parser.add_argument("--reply-to", help="要回复的帖子 id(可选)")
    parser.add_argument("--yes", action="store_true", help="确认发布;不带此参数只做预览")
    args = parser.parse_args()

    cost_label, has_url = estimate_cost(args.text)
    preview = {
        "text": args.text,
        "chars": len(args.text),
        "reply_to": args.reply_to,
        "estimated_cost": cost_label,
        "contains_url": has_url,
    }

    if not args.yes:
        print(json.dumps({"dry_run": True, **preview}, ensure_ascii=False, indent=2))
        print("\n未发布。确认无误后加 --yes 发布。", file=sys.stderr)
        return

    try:
        import tweepy  # noqa: F401
    except ImportError:
        print("错误:未安装 tweepy,先执行 pip3 install tweepy", file=sys.stderr)
        sys.exit(1)

    client = build_client()
    response = client.create_tweet(text=args.text,
                                   in_reply_to_tweet_id=args.reply_to or None)
    tweet_id = response.data["id"]
    print(json.dumps({"posted": True, "id": tweet_id,
                      "url": f"https://x.com/i/status/{tweet_id}", **preview},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
