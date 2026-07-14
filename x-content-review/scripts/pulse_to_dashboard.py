#!/usr/bin/env python3
"""把 pulse 数据(粉丝快照 + 最新分析 JSON)渲染进自媒体运营看板的 X-PULSE 标记段。

联动用:x-follower-snapshot(每天)和 x-weekly-report(每周)跑完后调用本脚本,
把「粉丝趋势 + 类别/时段效率 + A/B/C 分级」自动刷进看板,不再靠手动导 CSV。
口径是收藏/万曝光(pulse 公开 views),与看板 CSV 段的净涨粉口径并列、不混算。

只替换 <!-- X-PULSE:START --> 与 <!-- X-PULSE:END --> 之间的内容,标记外不动。
标记不存在时安全跳过(提示先给看板加标记),不破坏看板其余内容。

用法:
  python3 pulse_to_dashboard.py --dashboard <看板.md> [--data-dir <数据目录>]
  # 省略参数时用默认:数据目录 ~/.local/share/x-operation-skills,
  #                 看板 ~/Documents/knowledge-base/40-dashboards/自媒体运营看板.md
"""

import argparse
import glob
import json
import os

MARK_START = "<!-- X-PULSE:START -->"
MARK_END = "<!-- X-PULSE:END -->"
GRADE_LABELS = {
    "A": "A 高曝高藏 · 扩系列",
    "B": "B 低曝高藏 · 换头重发",
    "C": "C 双低 · 停选题",
}


def load_snapshots(data_dir):
    """读粉丝数快照 JSONL,按日期升序返回。"""
    path = os.path.join(data_dir, "x-follower-snapshots.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as snapshot_file:
        records = [json.loads(line) for line in snapshot_file if line.strip()]
    return sorted(records, key=lambda record: record.get("date", ""))


def load_latest_analysis(data_dir):
    """读最新的 x-analysis-*.json(按文件名日期),没有则返回 None。"""
    candidates = sorted(glob.glob(os.path.join(data_dir, "x-analysis-*.json")))
    if not candidates:
        return None
    with open(candidates[-1], encoding="utf-8") as analysis_file:
        return json.load(analysis_file)


def render_follower_trend(snapshots):
    """粉丝快照 → 趋势 markdown + 近 7 天涨粉(快照够才有)。"""
    if not snapshots:
        return "**粉丝趋势**:暂无快照(等每日 snapshot 积累)。"
    latest = snapshots[-1]
    lines = [f"**粉丝**:{latest['followers']}(截至 {latest['date']})"]
    # 近 7 天环比:找 ~7 天前的快照
    if len(snapshots) >= 2:
        from datetime import date
        latest_date = date.fromisoformat(latest["date"])
        prior = [s for s in snapshots
                 if (latest_date - date.fromisoformat(s["date"])).days >= 7]
        if prior:
            delta = latest["followers"] - prior[-1]["followers"]
            lines.append(f"· 近 7 天 {'+' if delta >= 0 else ''}{delta}")
        else:
            span = (latest_date - date.fromisoformat(snapshots[0]["date"])).days
            lines.append(f"· 快照跨度 {span} 天(满 7 天出周环比)")
    return " ".join(lines)


def render_analysis(analysis):
    """最新分析 JSON → 类别效率 / 时段 / 环比 / A-B-C markdown。"""
    if not analysis or "content" not in analysis:
        return ["**内容分析**:暂无(等每周 x-weekly-report 跑完)。"]
    content = analysis["content"]
    blocks = []

    comparison = content.get("period_comparison")
    if comparison and comparison.get("current_period"):
        cur, prev = comparison["current_period"], comparison["previous_period"]
        blocks.append(
            f"**本期 vs 上期**:发帖 {cur['posts']}/{prev['posts']} · "
            f"曝光 {cur['views']}/{prev['views']} · "
            f"效率(收藏/万曝光) {cur['bookmarks_per_10k_views']}/{prev['bookmarks_per_10k_views']}")
        blocks.append("")

    categories = [c for c in content.get("categories", [])
                  if c.get("category") != "reply" and c.get("posts", 0) >= 3]
    categories.sort(key=lambda c: -c.get("bookmarks_per_10k_views", 0))
    if categories:
        blocks.append("**类别效率(收藏/万曝光)**")
        blocks.append("")
        blocks.append("| 类别 | 帖 | 效率 |")
        blocks.append("|---|---|---|")
        for cat in categories:
            blocks.append(f"| {cat['category']} | {cat['posts']} | {cat['bookmarks_per_10k_views']} |")
        blocks.append("")

    slots = [s for s in content.get("time_slots_beijing", []) if s.get("posts", 0) >= 3]
    slots.sort(key=lambda s: -s.get("bookmarks_per_10k_views", 0))
    if slots:
        top_slots = "、".join(f"{s['slot_beijing']}({s['bookmarks_per_10k_views']})"
                             for s in slots[:3])
        blocks.append(f"**黄金时段(北京时间,样本≥3)**:{top_slots}")

    grade_b = content.get("repost_candidates_grade_b", [])
    if grade_b:
        blocks.append("")
        blocks.append(f"**{GRADE_LABELS['B']}**(换头重发候选):")
        for post in grade_b[:5]:
            metric = post.get("views", post.get("impressions", 0))
            blocks.append(f"- [{metric} 曝光 / {post.get('bookmarks', 0)} 收藏] {post.get('text', '')}")
    return blocks


def build_block(snapshots, analysis, generated_at):
    """组装 X-PULSE 段完整内容(标记之间的部分)。"""
    lines = [MARK_START,
             f"<!-- 由 pulse_to_dashboard.py 生成于 {generated_at},勿手改此段 -->",
             "",
             render_follower_trend(snapshots),
             ""]
    lines.extend(render_analysis(analysis))
    lines.append("")
    lines.append(MARK_END)
    return "\n".join(lines)


def write_block(dashboard_path, block):
    """把 block 替换进看板的 X-PULSE 标记段。标记缺失则安全跳过并返回 False。"""
    with open(dashboard_path, encoding="utf-8") as dashboard_file:
        text = dashboard_file.read()
    if MARK_START not in text or MARK_END not in text:
        return False
    before = text.split(MARK_START)[0]
    after = text.split(MARK_END, 1)[1]
    with open(dashboard_path, "w", encoding="utf-8") as dashboard_file:
        dashboard_file.write(before + block + after)
    return True


def main():
    default_data = os.environ.get("X_SKILLS_DATA_DIR") or os.path.expanduser(
        "~/.local/share/x-operation-skills")
    default_dash = os.path.expanduser(
        "~/Documents/knowledge-base/40-dashboards/自媒体运营看板.md")
    parser = argparse.ArgumentParser(description="pulse 数据 → 自媒体运营看板 X-PULSE 段")
    parser.add_argument("--data-dir", default=default_data)
    parser.add_argument("--dashboard", default=default_dash)
    parser.add_argument("--generated-at", default="", help="生成时间戳(runner 传入,避免脚本内取时间)")
    args = parser.parse_args()

    if not os.path.exists(args.dashboard):
        print(f"跳过:看板不存在 {args.dashboard}")
        return
    snapshots = load_snapshots(args.data_dir)
    analysis = load_latest_analysis(args.data_dir)
    block = build_block(snapshots, analysis, args.generated_at or "(未标注)")
    if write_block(args.dashboard, block):
        print(f"已刷新看板 X-PULSE 段:{args.dashboard}")
    else:
        print(f"跳过:看板缺 {MARK_START}/{MARK_END} 标记,先给看板加标记段")


if __name__ == "__main__":
    main()
