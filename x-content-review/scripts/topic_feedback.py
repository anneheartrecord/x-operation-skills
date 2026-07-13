#!/usr/bin/env python3
"""选题库回环:把复盘分析结果转成可合并进选题库的 markdown 块。

让复盘结论直接变成下一轮选题输入:
  - A 级帖(高曝光高收藏)→ 「值得扩成系列」建议
  - B 级帖(低曝光高收藏)→ 「换头重发」队列
  - 高效类别 → 「加大投产」提示

输入:analyze_x_data.py 输出的 analysis JSON。
输出:markdown(stdout),供 agent 审阅后合并进用户的 选题库.md,或直接落盘。

用法:
  python3 topic_feedback.py --analysis x-analysis.json
  python3 topic_feedback.py --analysis x-analysis.json --out 选题库-回环-YYYY-MM-DD.md
"""

import argparse
import json
import sys


def build_markdown(analysis):
    """把 analysis JSON 渲染成选题回环 markdown。"""
    content = analysis.get("content", {})
    generated_at = analysis.get("generated_at", "")
    lines = [f"# 选题库回环(自动生成 {generated_at})", ""]

    # 高效类别 → 加大投产
    categories = [c for c in content.get("categories", [])
                  if c["category"] not in ("reply",) and c.get("posts", 0) >= 3]
    rate_key = ("bookmarks_per_10k_views" if categories and
                "bookmarks_per_10k_views" in categories[0] else "follows_per_10k_impressions")
    categories.sort(key=lambda c: -c.get(rate_key, 0))
    if categories:
        lines.append("## 类别投产建议(按转化效率)")
        lines.append("")
        for index, cat in enumerate(categories):
            action = "⬆️ 加大投产" if index < 2 else ("⬇️ 减量或换角度" if index >= len(categories) - 1 else "维持")
            lines.append(f"- **{cat['category']}**:效率 {cat.get(rate_key, 0)}(帖 {cat['posts']}) → {action}")
        lines.append("")

    # A 级 → 扩系列
    top_posts = [p for p in content.get("window_top_posts", []) if p.get("grade") == "A"]
    if top_posts:
        lines.append("## A 级帖 → 扩成系列")
        lines.append("")
        lines.append("这些帖高曝光高收藏,是验证过的选题方向,围绕它们做系列:")
        lines.append("")
        for post in top_posts[:8]:
            metric = post.get("views", post.get("impressions", 0))
            lines.append(f"- [{metric} 曝光 / {post.get('bookmarks', 0)} 收藏] {post['text']}")
            if post.get("url"):
                lines.append(f"  - 原帖:{post['url']}")
        lines.append("")

    # B 级 → 换头重发队列
    repost = content.get("repost_candidates_grade_b", [])
    if repost:
        lines.append("## B 级帖 → 换头重发队列")
        lines.append("")
        lines.append("内容被收藏说明质量够,是开头/时机/曝光没跟上。重写钩子、挪到黄金档再发:")
        lines.append("")
        for post in repost[:8]:
            metric = post.get("views", post.get("impressions", 0))
            lines.append(f"- [ ] [{metric} 曝光 / {post.get('bookmarks', 0)} 收藏] {post['text']}")
            if post.get("url"):
                lines.append(f"  - 原帖:{post['url']}")
        lines.append("")

    if len(lines) <= 2:
        lines.append("(本次分析没有可回环的 A/B 级帖或足量类别,样本积累后再跑)")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="选题库回环(复盘结论 → 选题输入)")
    parser.add_argument("--analysis", required=True, help="analyze_x_data.py 输出的 JSON 路径")
    parser.add_argument("--out", help="输出 markdown 路径(不给则打印到 stdout)")
    args = parser.parse_args()

    with open(args.analysis, encoding="utf-8") as analysis_file:
        analysis = json.load(analysis_file)

    markdown = build_markdown(analysis)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as out_file:
            out_file.write(markdown + "\n")
        print(f"已写入 {args.out}", file=sys.stderr)
    else:
        print(markdown)


if __name__ == "__main__":
    main()
