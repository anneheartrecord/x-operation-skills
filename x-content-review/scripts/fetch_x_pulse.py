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


def resolve_data_dir():
    """twscrape 状态库(accounts.db)与快照的存放目录。

    默认 ~/.local/share/x-operation-skills,可用 X_SKILLS_DATA_DIR 覆盖。
    刻意不放知识库运营目录:accounts.db 含登录态,避免误提交进 git。
    """
    data_dir = os.environ.get("X_SKILLS_DATA_DIR") or os.path.expanduser(
        "~/.local/share/x-operation-skills")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def download_media(media_urls, target_dir):
    """把头像/banner 等图片经代理下载到本地,返回 {名称: 本地路径}。供账号诊断看图。"""
    import curl_cffi

    proxy = resolve_proxy()
    os.makedirs(target_dir, exist_ok=True)
    saved = {}
    for name, url in media_urls.items():
        if not url:
            continue
        # 头像 URL 常带 _normal 后缀是小图,换成原图
        full_url = url.replace("_normal.", ".")
        # 取扩展名:必须是最后一段路径里的纯后缀(banner URL 无后缀,回退 jpg)
        last_segment = full_url.split("?")[0].rsplit("/", 1)[-1]
        extension = last_segment.rsplit(".", 1)[-1] if "." in last_segment else "jpg"
        if not extension.isalnum() or len(extension) > 4:
            extension = "jpg"
        local_path = os.path.join(target_dir, f"{name}.{extension}")
        response = curl_cffi.requests.get(full_url, proxy=proxy, timeout=20)
        if response.status_code == 200:
            with open(local_path, "wb") as image_file:
                image_file.write(response.content)
            saved[name] = local_path
    return saved


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
    api = API(os.path.join(resolve_data_dir(), "accounts.db"), proxy=proxy)
    cookie_string = f"auth_token={auth_token}; ct0={ct0}"
    # twscrape 的 add_account 遇已存在账号会 no-op,不会刷新 cookie。为保证 env 里
    # 当前(可能刚更新过)的 cookie 一定生效,先删后加。单账号日/周跑,丢失限流状态可忽略。
    try:
        await api.pool.delete_accounts([username])
    except Exception:  # 账号不存在等,忽略
        pass
    await api.pool.add_account(username, "-", "-", "-",
                              cookies=cookie_string, proxy=proxy)
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


# X web app 的公开 bearer(所有网页客户端共用的常量),鉴权靠 cookie 而非它
_X_WEB_BEARER = ("AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
                 "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA")


def check_cookie():
    """cookie 健康检查,返回 (ok, 说明)。真正测鉴权,不测公开可达性。

    公开端点(如 UserByScreenName)用无效 cookie 也能返回,不能用来判活;这里打一个
    鉴权门后端点:401(code 32 Could not authenticate)= cookie 失效;连接异常 = 代理/网络
    问题;其余(200/404 等已过鉴权)= cookie 有效。
    """
    from curl_cffi import requests

    auth_token = os.environ.get("X_AUTH_TOKEN", "")
    ct0 = os.environ.get("X_CT0", "")
    if not auth_token or not ct0:
        return False, "缺少 X_AUTH_TOKEN / X_CT0 环境变量,先按 README 配置 cookie。"

    proxy = resolve_proxy()
    headers = {
        "authorization": f"Bearer {_X_WEB_BEARER}",
        "x-csrf-token": ct0,
        "cookie": f"auth_token={auth_token}; ct0={ct0}",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
    }
    try:
        response = requests.get("https://api.x.com/1.1/account/settings.json",
                                headers=headers, proxy=proxy, timeout=15,
                                impersonate="chrome")
    except Exception as error:  # 连接/代理层异常
        return False, (f"网络或代理异常:{type(error).__name__}: {error}。"
                       "检查 X_PROXY(如 http://127.0.0.1:7890)是否可用。")
    if response.status_code == 401:
        return False, ("cookie 已失效(登出或改密)。重新登录 x.com,按 README 重新复制 "
                       "auth_token 和 ct0 到 ~/.config/secrets/api-keys.env。")
    return True, f"cookie 有效(鉴权端点返回 {response.status_code},已过鉴权门)。"


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
    parser.add_argument("--download-media",
                        help="配合 --profile:把头像/banner 下载到该目录,返回本地路径供看图")
    parser.add_argument("--check", action="store_true",
                        help="cookie 健康检查:有效打印 OK 退出 0,失效/网络异常打印原因退出 1")
    args = parser.parse_args()

    try:
        import twscrape  # noqa: F401
    except ImportError:
        print("错误:未安装 twscrape,先执行 pip3 install twscrape curl_cffi", file=sys.stderr)
        sys.exit(1)

    if args.check:
        ok, message = check_cookie()
        print(("OK: " if ok else "FAIL: ") + message, file=sys.stderr)
        sys.exit(0 if ok else 1)

    if args.profile:
        result = asyncio.run(fetch_profile(args.user))
        if args.download_media:
            result["local_media"] = download_media(
                {"avatar": result.get("avatar_url"), "banner": result.get("banner_url")},
                args.download_media)
    else:
        result = asyncio.run(fetch_recent_posts(args.user, args.limit))
        if args.snapshot_file:
            append_follower_snapshot(args.snapshot_file, result["followers"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
