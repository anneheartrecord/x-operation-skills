#!/usr/bin/env python3
"""X 定时发帖排期器(cookie 模式):把一批文稿排进 X 原生定时队列。

原理:用登录 cookie 调 X 网页端内部 GraphQL 的 CreateScheduledTweet,帖子进入
x.com「未发送的帖子 → 已排定」队列,到点由 X 服务器发布。用户随时可在网页端
审改删——这是保留最后审核权的排期方式,不是本机到点硬发。

⚠️ 非官方接口,注意:
  - queryId 会随 X 前端版本更换,失效时报 404;从浏览器 DevTools 的
    graphql 请求里抓新 id 更新本文件顶部常量即可。
  - 保持低频(每天几条),行为与网页端手动排定时无异;不要批量高频调用。

登录态来自环境变量(与 x-content-review 同一套,存 ~/.config/secrets/api-keys.env):
  X_AUTH_TOKEN / X_CT0 / X_PROXY(国内必需)

用法:
  # 1. dry-run:出排期计划(默认,不碰网络)
  python3 schedule_tweets.py --drafts a.md b.md --start-date 2026-07-21
  python3 schedule_tweets.py --drafts-dir ~/drafts/
  # 2. 用户确认计划后真正排期
  python3 schedule_tweets.py --drafts a.md b.md --start-date 2026-07-21 --yes
  # 3. 队列管理
  python3 schedule_tweets.py --list          # 看当前定时队列
  python3 schedule_tweets.py --delete <id>   # 删一条排期
"""

import argparse
import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

TZ_BEIJING = timezone(timedelta(hours=8))
# 默认发帖时段(北京时间整点,2026-07-20 用户定稿)
DEFAULT_SLOTS = (11, 14, 20, 23)
# X 单帖加权长度上限;留安全余量与 x-post 的 thread 口径一致
WEIGHT_LIMIT = 280
URL_PATTERN = re.compile(r"https?://\S+")
# t.co 短链固定按 23 字符计长
TCO_WEIGHT = 23

# X web app 公开 bearer(网页客户端共用常量,鉴权靠 cookie 而非它)
_X_WEB_BEARER = ("AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
                 "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA")
# GraphQL queryId(随 X 前端版本更换,失效报 404 时从 DevTools 抓新值)
QUERY_ID_CREATE = "LCVzRQGxOaGnOnYH01NQXg"
QUERY_ID_FETCH = "ITtjAzvlZni2wWXwf295Qg"
QUERY_ID_DELETE = "CTOVqej0JBXAZSwkp1US0g"
GRAPHQL_BASE = "https://x.com/i/api/graphql"


def weighted_len(text):
    """X 加权字符长度:URL 按 t.co 固定 23 计,其余非 ASCII 算 2、ASCII 算 1。"""
    normalized = URL_PATTERN.sub("\x00" * TCO_WEIGHT, text)
    return sum(1 if ord(char) < 0x100 else 2 for char in normalized)


def strip_frontmatter(text):
    """去掉 markdown 文件头部的 YAML frontmatter,返回正文。"""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def load_drafts(paths):
    """读取文稿文件列表,返回 [{name, text, weighted_len, over_limit}]。"""
    drafts = []
    for path in paths:
        with open(path, encoding="utf-8") as draft_file:
            body = strip_frontmatter(draft_file.read()).strip()
        length = weighted_len(body)
        drafts.append({
            "name": os.path.basename(path),
            "text": body,
            "weighted_len": length,
            "over_limit": length > WEIGHT_LIMIT,
        })
    return drafts


def build_plan(drafts, now, slots=DEFAULT_SLOTS, start_date=None, margin_minutes=10):
    """把文稿按顺序排进「每天固定时段」的计划表。

    参数:drafts 为 load_drafts 的产物;now 为当前北京时间(datetime,含 tzinfo);
    slots 为北京时间整点小时列表;start_date(date)不传则从今天开始。
    规则:跳过已过去(或距 now 不足 margin_minutes)的时段,顺延到之后的档;
    每天最多 len(slots) 条,排满自动进入下一天。
    返回 plan 列表,每项含 scheduled_at(ISO)与 execute_at(epoch 秒)。
    """
    plan = []
    day = start_date or now.date()
    slot_iter_day, slot_index = day, 0
    ordered_slots = sorted(slots)
    for draft in drafts:
        while True:
            hour = ordered_slots[slot_index]
            candidate = datetime(slot_iter_day.year, slot_iter_day.month,
                                 slot_iter_day.day, hour, 0, tzinfo=TZ_BEIJING)
            slot_index += 1
            if slot_index >= len(ordered_slots):
                slot_index = 0
                slot_iter_day = slot_iter_day + timedelta(days=1)
            if candidate >= now + timedelta(minutes=margin_minutes):
                break
        plan.append({**draft,
                     "scheduled_at": candidate.strftime("%Y-%m-%d %H:%M"),
                     "execute_at": int(candidate.timestamp())})
    return plan


def build_create_payload(text, execute_at):
    """组装 CreateScheduledTweet 的请求体。"""
    return {
        "variables": {
            "post_tweet_request": {
                "auto_populate_reply_metadata": False,
                "status": text,
                "exclude_reply_user_ids": [],
                "media_ids": [],
            },
            "execute_at": execute_at,
        },
        "queryId": QUERY_ID_CREATE,
    }


def resolve_proxy():
    """解析代理地址(国内访问 X 必需):优先 X_PROXY,退回 HTTPS_PROXY/HTTP_PROXY。"""
    return (os.environ.get("X_PROXY") or os.environ.get("HTTPS_PROXY")
            or os.environ.get("HTTP_PROXY") or None)


def build_headers():
    """组装 cookie 鉴权请求头;缺环境变量时报错退出。"""
    auth_token = os.environ.get("X_AUTH_TOKEN", "")
    ct0 = os.environ.get("X_CT0", "")
    if not auth_token or not ct0:
        print("错误:缺少 X_AUTH_TOKEN / X_CT0 环境变量(配置方法见 x-content-review README)。",
              file=sys.stderr)
        sys.exit(1)
    return {
        "authorization": f"Bearer {_X_WEB_BEARER}",
        "x-csrf-token": ct0,
        "cookie": f"auth_token={auth_token}; ct0={ct0}",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "content-type": "application/json",
    }


def graphql_request(method, query_id, operation, payload=None, params=None):
    """发一个 GraphQL 请求,返回 (status_code, 响应 JSON 或文本)。"""
    from curl_cffi import requests

    url = f"{GRAPHQL_BASE}/{query_id}/{operation}"
    kwargs = {"headers": build_headers(), "proxy": resolve_proxy(),
              "timeout": 20, "impersonate": "chrome"}
    if method == "POST":
        response = requests.post(url, json=payload, **kwargs)
    else:
        response = requests.get(url, params=params, **kwargs)
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, {"raw": response.text[:500]}


def create_scheduled(text, execute_at):
    """排一条定时帖,成功返回 scheduled_tweet_id,失败返回 None 并打印错误。"""
    status, body = graphql_request("POST", QUERY_ID_CREATE, "CreateScheduledTweet",
                                   payload=build_create_payload(text, execute_at))
    rest_id = (body.get("data", {}).get("tweet", {}) or {}).get("rest_id")
    if status == 200 and rest_id:
        return rest_id
    hint = ""
    if status == 404:
        hint = "(queryId 可能已过期,从浏览器 DevTools 的 graphql 请求里抓新 id 更新脚本常量)"
    print(f"排期失败 HTTP {status}{hint}: {json.dumps(body, ensure_ascii=False)[:300]}",
          file=sys.stderr)
    return None


def list_scheduled():
    """拉取当前定时队列,返回原始 JSON。"""
    params = {"variables": json.dumps({"ascending": True})}
    status, body = graphql_request("GET", QUERY_ID_FETCH, "FetchScheduledTweets",
                                   params=params)
    if status != 200:
        print(f"拉取队列失败 HTTP {status}: {json.dumps(body, ensure_ascii=False)[:300]}",
              file=sys.stderr)
        sys.exit(1)
    return body


def delete_scheduled(scheduled_id):
    """删除一条定时帖,返回是否成功。"""
    payload = {"variables": {"scheduled_tweet_id": scheduled_id},
               "queryId": QUERY_ID_DELETE}
    status, body = graphql_request("POST", QUERY_ID_DELETE, "DeleteScheduledTweet",
                                   payload=payload)
    if status == 200:
        return True
    print(f"删除失败 HTTP {status}: {json.dumps(body, ensure_ascii=False)[:300]}",
          file=sys.stderr)
    return False


def collect_draft_paths(args):
    """从 --drafts / --drafts-dir 收集文稿路径(目录按文件名排序)。"""
    paths = list(args.drafts or [])
    if args.drafts_dir:
        paths.extend(sorted(glob.glob(os.path.join(args.drafts_dir, "*.md")) +
                            glob.glob(os.path.join(args.drafts_dir, "*.txt"))))
    if not paths:
        print("错误:--drafts 或 --drafts-dir 至少提供一个文稿。", file=sys.stderr)
        sys.exit(1)
    return paths


def main():
    parser = argparse.ArgumentParser(description="X 定时发帖排期(cookie · X 原生定时队列)")
    parser.add_argument("--drafts", nargs="*", help="文稿文件路径列表(每个文件一条帖)")
    parser.add_argument("--drafts-dir", help="文稿目录(取 *.md / *.txt,按文件名排序)")
    parser.add_argument("--start-date", help="排期起始日 YYYY-MM-DD(默认今天)")
    parser.add_argument("--slots", default=",".join(str(s) for s in DEFAULT_SLOTS),
                        help=f"每日发帖时段(北京时间整点,逗号分隔,默认 {DEFAULT_SLOTS})")
    parser.add_argument("--yes", action="store_true",
                        help="确认后真正排期(默认 dry-run 只出计划)")
    parser.add_argument("--list", action="store_true", help="查看当前定时队列")
    parser.add_argument("--delete", metavar="ID", help="删除指定 scheduled_tweet_id")
    args = parser.parse_args()

    if args.list:
        print(json.dumps(list_scheduled(), ensure_ascii=False, indent=2))
        return
    if args.delete:
        sys.exit(0 if delete_scheduled(args.delete) else 1)

    drafts = load_drafts(collect_draft_paths(args))
    slots = tuple(int(part) for part in args.slots.split(","))
    start_date = (datetime.strptime(args.start_date, "%Y-%m-%d").date()
                  if args.start_date else None)
    plan = build_plan(drafts, datetime.now(TZ_BEIJING), slots, start_date)

    over_limit = [item["name"] for item in plan if item["over_limit"]]
    preview = [{"name": item["name"], "scheduled_at": item["scheduled_at"],
                "weighted_len": item["weighted_len"], "over_limit": item["over_limit"],
                "preview": item["text"][:60]} for item in plan]
    if not args.yes:
        print(json.dumps({"dry_run": True, "count": len(plan),
                          "slots_beijing": sorted(slots), "plan": preview},
                         ensure_ascii=False, indent=2))
        if over_limit:
            print(f"⚠️ 超长(>{WEIGHT_LIMIT} 加权字符)不可发,先改稿:{over_limit}",
                  file=sys.stderr)
        return

    if over_limit:
        print(f"错误:以下文稿超长,拒绝排期:{over_limit}", file=sys.stderr)
        sys.exit(1)
    results = []
    for item in plan:
        scheduled_id = create_scheduled(item["text"], item["execute_at"])
        if not scheduled_id:
            print(f"在「{item['name']}」处中止,已排 {len(results)} 条(不自动重试)。",
                  file=sys.stderr)
            break
        results.append({"name": item["name"], "scheduled_at": item["scheduled_at"],
                        "scheduled_tweet_id": scheduled_id})
        time.sleep(2)  # 低频礼貌间隔
    print(json.dumps({"scheduled": results}, ensure_ascii=False, indent=2))
    if len(results) < len(plan):
        sys.exit(1)


if __name__ == "__main__":
    main()
