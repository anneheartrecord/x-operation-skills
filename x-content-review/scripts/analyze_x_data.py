#!/usr/bin/env python3
"""X(Twitter) 账号数据复盘分析器。

输入:X Analytics 导出的两类 CSV
  - overview CSV: 日度总览(Impressions/New follows/Create Post 等)
  - content CSV:  单帖明细(Post id/Post text/Impressions/New follows 等)

输出:JSON(stdout),包含周度趋势、发帖时段分析、内容类别转化、单帖 A/B/C 分级。
发帖时间从 Post id(Snowflake ID)反推,精确到秒,按北京时间(UTC+8)分桶。

用法:
  python3 analyze_x_data.py --overview overview.csv --content content.csv \
      [--days 7] [--categories categories.json]
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# Twitter Snowflake 纪元(毫秒)
TWITTER_EPOCH_MS = 1288834974657
TZ_BEIJING = timezone(timedelta(hours=8))

# 默认内容类别关键词表(可用 --categories 传 JSON 覆盖)
# 匹配顺序即优先级;reply 由「正文以 @ 开头」单独判断,优先级最高
DEFAULT_CATEGORIES = {
    "投资": ["投资", "美股", "持仓", "仓位", "定投", "复利", "股票", "纳指", "标普", "财富"],
    "开户出入金": ["开户", "入金", "出金", "长桥", "券商", "汇款", "换汇"],
    "AI工程": ["claude", "codex", "agent", "llm", "prompt", "mcp", "skill", "cursor",
               "openai", "anthropic", "源码", "工作流", "ai"],
    "职业成长": ["晋升", "跳槽", "面试", "职场", "工资", "薪资", "offer", "程序员", "工程师", "成长"],
}


def parse_analytics_date(raw_date):
    """解析 X Analytics 的日期格式 "Fri, Jul 10, 2026" -> datetime.date。"""
    return datetime.strptime(raw_date.strip(), "%a, %b %d, %Y").date()


def snowflake_to_beijing_time(post_id):
    """从 Snowflake Post id 反推发帖时间,返回北京时间 datetime。"""
    epoch_ms = (int(post_id) >> 22) + TWITTER_EPOCH_MS
    return datetime.fromtimestamp(epoch_ms / 1000, tz=TZ_BEIJING)


def read_csv_rows(csv_path):
    """读取 CSV 为 dict 列表,自动去 BOM。"""
    with open(csv_path, newline="", encoding="utf-8-sig") as file_handle:
        return list(csv.DictReader(file_handle))


def to_int(raw_value):
    """容错地把 CSV 单元格转 int,空值/异常返回 0。"""
    try:
        return int(str(raw_value).replace(",", "").strip() or 0)
    except ValueError:
        return 0


def classify_post(post_text, category_keywords):
    """按关键词表给单帖分类;以 @ 开头视为 reply,无命中归「其他」。"""
    if post_text.strip().startswith("@"):
        return "reply"
    lowered_text = post_text.lower()
    for category_name, keywords in category_keywords.items():
        if any(keyword.lower() in lowered_text for keyword in keywords):
            return category_name
    return "其他"


def grade_post(impressions, bookmarks, median_impressions):
    """单帖 A/B/C 分级:A=高曝光高收藏(扩系列) B=低曝光高收藏(换头重发) C=双低(停选题)。"""
    high_exposure = impressions >= max(median_impressions * 2, 1)
    high_bookmark = bookmarks >= 3
    if high_exposure and high_bookmark:
        return "A"
    if high_bookmark:
        return "B"
    if not high_exposure and bookmarks == 0 and impressions < median_impressions:
        return "C"
    return "-"


def analyze_overview(overview_rows, window_days, today):
    """日度总览:窗口内每日指标 + 按周聚合趋势(周一为一周起点)。"""
    daily_records = []
    for row in overview_rows:
        record_date = parse_analytics_date(row["Date"])
        daily_records.append({
            "date": record_date.isoformat(),
            "impressions": to_int(row.get("Impressions")),
            "new_follows": to_int(row.get("New follows")),
            "unfollows": to_int(row.get("Unfollows")),
            "posts": to_int(row.get("Create Post")),
            "profile_visits": to_int(row.get("Profile visits")),
        })
    daily_records.sort(key=lambda record: record["date"])

    weekly_trend = defaultdict(lambda: {"impressions": 0, "net_follows": 0, "posts": 0})
    for record in daily_records:
        record_date = datetime.fromisoformat(record["date"]).date()
        week_start = (record_date - timedelta(days=record_date.weekday())).isoformat()
        weekly_trend[week_start]["impressions"] += record["impressions"]
        weekly_trend[week_start]["net_follows"] += record["new_follows"] - record["unfollows"]
        weekly_trend[week_start]["posts"] += record["posts"]

    window_start = today - timedelta(days=window_days)
    window_records = [record for record in daily_records
                      if datetime.fromisoformat(record["date"]).date() >= window_start]
    window_net_follows = sum(r["new_follows"] - r["unfollows"] for r in window_records)
    return {
        "window_daily": window_records,
        "window_summary": {
            "days": len(window_records),
            "impressions": sum(r["impressions"] for r in window_records),
            "net_follows": window_net_follows,
            "avg_daily_net_follows": round(window_net_follows / len(window_records), 1)
            if window_records else 0,
            "posts": sum(r["posts"] for r in window_records),
        },
        "weekly_trend": [{"week_start": week, **metrics}
                         for week, metrics in sorted(weekly_trend.items())],
    }


def analyze_content(content_rows, window_days, today, category_keywords):
    """单帖明细:时段分析(北京时间) + 类别转化(涨粉/万曝光) + A/B/C 分级。"""
    window_start = today - timedelta(days=window_days)
    posts = []
    for row in content_rows:
        posted_at = snowflake_to_beijing_time(row["Post id"])
        posts.append({
            "id": row["Post id"],
            "posted_at": posted_at.strftime("%Y-%m-%d %H:%M"),
            "hour": posted_at.hour,
            "weekday": posted_at.strftime("%a"),
            "text": re.sub(r"\s+", " ", row.get("Post text", ""))[:60],
            "link": row.get("Post Link", ""),
            "impressions": to_int(row.get("Impressions")),
            "likes": to_int(row.get("Likes")),
            "bookmarks": to_int(row.get("Bookmarks")),
            "new_follows": to_int(row.get("New follows")),
            "profile_visits": to_int(row.get("Profile visits")),
            "category": classify_post(row.get("Post text", ""), category_keywords),
            "in_window": posted_at.date() >= window_start,
        })

    original_posts = [post for post in posts if post["category"] != "reply"]

    # 时段分析:2 小时一桶,只统计非 reply 原创帖
    slot_stats = defaultdict(lambda: {"posts": 0, "impressions": 0, "new_follows": 0})
    for post in original_posts:
        slot_label = f"{post['hour'] // 2 * 2:02d}-{post['hour'] // 2 * 2 + 2:02d}"
        slot_stats[slot_label]["posts"] += 1
        slot_stats[slot_label]["impressions"] += post["impressions"]
        slot_stats[slot_label]["new_follows"] += post["new_follows"]
    time_slots = []
    for slot_label, metrics in sorted(slot_stats.items()):
        follows_per_10k = (metrics["new_follows"] / metrics["impressions"] * 10000
                           if metrics["impressions"] else 0)
        time_slots.append({"slot_beijing": slot_label, **metrics,
                           "avg_impressions": round(metrics["impressions"] / metrics["posts"]),
                           "follows_per_10k_impressions": round(follows_per_10k, 1)})

    # 类别转化:涨粉/万曝光
    category_stats = defaultdict(lambda: {"posts": 0, "impressions": 0, "new_follows": 0})
    for post in posts:
        category_stats[post["category"]]["posts"] += 1
        category_stats[post["category"]]["impressions"] += post["impressions"]
        category_stats[post["category"]]["new_follows"] += post["new_follows"]
    categories = []
    for category_name, metrics in sorted(category_stats.items(),
                                         key=lambda item: -item[1]["impressions"]):
        follows_per_10k = (metrics["new_follows"] / metrics["impressions"] * 10000
                           if metrics["impressions"] else 0)
        categories.append({"category": category_name, **metrics,
                           "follows_per_10k_impressions": round(follows_per_10k, 1)})

    # A/B/C 分级(基于原创帖曝光中位数)
    sorted_impressions = sorted(post["impressions"] for post in original_posts) or [0]
    median_impressions = sorted_impressions[len(sorted_impressions) // 2]
    for post in original_posts:
        post["grade"] = grade_post(post["impressions"], post["bookmarks"], median_impressions)

    window_originals = [post for post in original_posts if post["in_window"]]
    top_posts = sorted(window_originals, key=lambda post: -post["impressions"])[:10]
    graded_b = [post for post in original_posts if post.get("grade") == "B"][:5]
    return {
        "post_count_total": len(posts),
        "original_count": len(original_posts),
        "median_impressions": median_impressions,
        "time_slots_beijing": time_slots,
        "categories": categories,
        "window_top_posts": top_posts,
        "repost_candidates_grade_b": graded_b,
    }


def analyze_pulse(pulse_data, window_days, today, category_keywords, snapshot_path):
    """Pulse 模式分析:基于公开指标(views/收藏),口径为「收藏/万曝光」。

    没有 analytics 后台的净涨粉与主页访问;涨粉趋势来自粉丝数快照 JSONL(若提供)。
    """
    window_start = today - timedelta(days=window_days)
    posts = []
    for raw_post in pulse_data.get("posts", []):
        posted_at = datetime.fromisoformat(raw_post["posted_at"]).astimezone(TZ_BEIJING)
        post_text = raw_post.get("text", "")
        posts.append({
            "id": raw_post["id"],
            "posted_at": posted_at.strftime("%Y-%m-%d %H:%M"),
            "hour": posted_at.hour,
            "views": raw_post.get("views") or 0,
            "likes": raw_post.get("likes") or 0,
            "bookmarks": raw_post.get("bookmarks") or 0,
            "text": re.sub(r"\s+", " ", post_text)[:60],
            "url": raw_post.get("url", ""),
            "category": classify_post(post_text, category_keywords),
            "in_window": posted_at.date() >= window_start,
        })
    original_posts = [post for post in posts if post["category"] != "reply"]

    slot_stats = defaultdict(lambda: {"posts": 0, "views": 0, "bookmarks": 0})
    category_stats = defaultdict(lambda: {"posts": 0, "views": 0, "bookmarks": 0})
    for post in original_posts:
        slot_label = f"{post['hour'] // 2 * 2:02d}-{post['hour'] // 2 * 2 + 2:02d}"
        slot_stats[slot_label]["posts"] += 1
        slot_stats[slot_label]["views"] += post["views"]
        slot_stats[slot_label]["bookmarks"] += post["bookmarks"]
    for post in posts:
        category_stats[post["category"]]["posts"] += 1
        category_stats[post["category"]]["views"] += post["views"]
        category_stats[post["category"]]["bookmarks"] += post["bookmarks"]

    def with_bookmark_rate(metrics):
        """补充「收藏/万曝光」比率字段。"""
        rate = metrics["bookmarks"] / metrics["views"] * 10000 if metrics["views"] else 0
        return {**metrics, "bookmarks_per_10k_views": round(rate, 1)}

    sorted_views = sorted(post["views"] for post in original_posts) or [0]
    median_views = sorted_views[len(sorted_views) // 2]
    for post in original_posts:
        post["grade"] = grade_post(post["views"], post["bookmarks"], median_views)

    follower_trend = []
    if snapshot_path:
        try:
            with open(snapshot_path, encoding="utf-8") as snapshot_file:
                follower_trend = [json.loads(line) for line in snapshot_file if line.strip()]
        except FileNotFoundError:
            pass

    return {
        "metric_note": "pulse 模式无净涨粉数据,口径为 收藏/万曝光(views);涨粉看 follower_trend 快照差值",
        "followers_now": pulse_data.get("followers"),
        "follower_trend": follower_trend,
        "post_count_total": len(posts),
        "original_count": len(original_posts),
        "median_views": median_views,
        "time_slots_beijing": [{"slot_beijing": slot, **with_bookmark_rate(metrics)}
                               for slot, metrics in sorted(slot_stats.items())],
        "categories": [{"category": name, **with_bookmark_rate(metrics)}
                       for name, metrics in sorted(category_stats.items(),
                                                   key=lambda item: -item[1]["views"])],
        "window_top_posts": sorted([p for p in original_posts if p["in_window"]],
                                   key=lambda post: -post["views"])[:10],
        "repost_candidates_grade_b": [p for p in original_posts if p.get("grade") == "B"][:5],
    }


def main():
    parser = argparse.ArgumentParser(description="X 账号数据复盘分析(pulse 模式或 CSV 模式)")
    parser.add_argument("--pulse", help="fetch_x_pulse.py 输出的 JSON 路径(pulse 模式,默认路径)")
    parser.add_argument("--snapshots", help="粉丝数快照 JSONL 路径(pulse 模式可选)")
    parser.add_argument("--overview", help="日度总览 CSV 路径(CSV 模式)")
    parser.add_argument("--content", help="单帖明细 CSV 路径(CSV 模式)")
    parser.add_argument("--days", type=int, default=7, help="复盘窗口天数(默认 7)")
    parser.add_argument("--categories", help="类别关键词 JSON 路径(可选,覆盖默认表)")
    args = parser.parse_args()

    category_keywords = DEFAULT_CATEGORIES
    if args.categories:
        with open(args.categories, encoding="utf-8") as keywords_file:
            category_keywords = json.load(keywords_file)

    today = datetime.now(TZ_BEIJING).date()
    result = {
        "generated_at": datetime.now(TZ_BEIJING).strftime("%Y-%m-%d %H:%M %z"),
        "window_days": args.days,
    }

    if args.pulse:
        with open(args.pulse, encoding="utf-8") as pulse_file:
            pulse_data = json.load(pulse_file)
        result["mode"] = "pulse"
        result["content"] = analyze_pulse(pulse_data, args.days, today,
                                          category_keywords, args.snapshots)
    elif args.overview and args.content:
        overview_rows = read_csv_rows(args.overview)
        content_rows = read_csv_rows(args.content)
        if not overview_rows or not content_rows:
            print("错误:CSV 为空或表头不匹配", file=sys.stderr)
            sys.exit(1)
        result["mode"] = "csv"
        result["overview"] = analyze_overview(overview_rows, args.days, today)
        result["content"] = analyze_content(content_rows, args.days, today, category_keywords)
    else:
        print("错误:需提供 --pulse,或同时提供 --overview 与 --content", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
