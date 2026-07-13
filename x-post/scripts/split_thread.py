#!/usr/bin/env python3
"""长文智能拆分成 X thread:按句界切成合规长度,链接统一放末条自回复以省溢价。

两个设计要点:
  1. X 计长是「加权字符」:CJK/全角算 2,ASCII 算 1,上限 280。这里按加权长度切,
     并留安全余量(默认 270),避免中文帖超长发布失败。
  2. 计费:每条含链接帖 $0.20 vs 纯文字 $0.015。把所有链接抽到最后一条自回复,
     正文各条保持纯文字,整个 thread 只有 1 条付 $0.20,其余 $0.015。

输入:一个 markdown/文本文件(段落用空行分隔)。
输出:thread plan JSON(stdout),含每条正文、加权长度、末条链接自回复、预估总价。
供 x-post 的 --thread-file 顺序发布。

用法:
  python3 split_thread.py --file draft.md [--limit 270] [--number]
"""

import argparse
import json
import re
import sys

URL_PATTERN = re.compile(r"https?://\S+")


def weighted_len(text):
    """X 加权字符长度:非 ASCII(含中文/全角/emoji)算 2,ASCII 算 1。"""
    return sum(1 if ord(char) < 0x100 else 2 for char in text)


def split_sentences(paragraph):
    """把段落按中英文句末标点切成句子,保留标点。"""
    parts = re.split(r"(?<=[。!?!?\n])", paragraph)
    return [part.strip() for part in parts if part.strip()]


def pack_segments(text, weight_limit):
    """把正文按句子贪心装箱成多条 ≤ weight_limit(加权)的推文。"""
    segments, current = [], ""
    for paragraph in [block for block in text.split("\n\n") if block.strip()]:
        for sentence in split_sentences(paragraph):
            # 单句就超限:硬切(尽量在空格处),避免死循环
            while weighted_len(sentence) > weight_limit:
                cut = _hard_cut(sentence, weight_limit)
                if current:
                    segments.append(current)
                    current = ""
                segments.append(cut)
                sentence = sentence[len(cut):].strip()
            candidate = (current + " " + sentence).strip() if current else sentence
            if weighted_len(candidate) <= weight_limit:
                current = candidate
            else:
                segments.append(current)
                current = sentence
    if current:
        segments.append(current)
    return segments


def _hard_cut(sentence, weight_limit):
    """对超长单句在加权上限内硬切,优先切在最后一个空格处。"""
    cut = ""
    for char in sentence:
        if weighted_len(cut + char) > weight_limit:
            break
        cut += char
    last_space = cut.rfind(" ")
    if last_space > weight_limit // 2:  # 有像样的空格才在空格切
        cut = cut[:last_space]
    return cut.strip()


def build_thread(text, weight_limit, number):
    """把正文拆成 thread:抽链接到末条自回复,正文各条纯文字,附加权长度与预估价。"""
    links = URL_PATTERN.findall(text)
    body = URL_PATTERN.sub("", text)  # 正文去链接,链接进末条
    body = re.sub(r"[ \t]+", " ", body)

    segments = pack_segments(body, weight_limit)
    if number and len(segments) > 1:
        total = len(segments)
        segments = [f"{seg}\n\n{index}/{total}" for index, seg in enumerate(segments, 1)]

    tweets = [{"text": seg, "weighted_len": weighted_len(seg), "has_link": False}
              for seg in segments]
    # 链接统一放末条自回复
    if links:
        link_text = "相关链接:\n" + "\n".join(dict.fromkeys(links))  # 去重保序
        tweets.append({"text": link_text, "weighted_len": weighted_len(link_text),
                       "has_link": True})

    link_tweets = sum(1 for t in tweets if t["has_link"])
    cost = link_tweets * 0.20 + (len(tweets) - link_tweets) * 0.015
    return {
        "tweet_count": len(tweets),
        "link_tweets": link_tweets,
        "estimated_cost_usd": round(cost, 3),
        "cost_note": "链接已归拢到末条自回复;只有它付 $0.20,正文各条 $0.015",
        "tweets": tweets,
    }


def main():
    parser = argparse.ArgumentParser(description="长文拆 X thread(句界切分 + 链接省溢价)")
    parser.add_argument("--file", required=True, help="长文文件路径(markdown/文本)")
    parser.add_argument("--limit", type=int, default=270,
                        help="单条加权长度上限(默认 270,X 上限 280 留余量)")
    parser.add_argument("--number", action="store_true", help="给每条加 i/n 编号")
    parser.add_argument("--out", help="thread plan 输出路径(不给则打印 stdout)")
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as draft_file:
        text = draft_file.read().strip()
    if not text:
        print("错误:文件为空", file=sys.stderr)
        sys.exit(1)

    plan = build_thread(text, args.limit, args.number)
    output = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as out_file:
            out_file.write(output + "\n")
        print(f"已写入 {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
