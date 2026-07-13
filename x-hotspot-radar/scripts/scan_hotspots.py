#!/usr/bin/env python3
"""热点扫描查询生成器:按账号定位的领域,产出一批 WebSearch/WebFetch 查询建议。

本脚本不联网,只把「今天该搜什么」结构化出来;真正的抓取由 agent 用
WebSearch/WebFetch 执行(agent 有这些工具,脚本没有)。这样热点来源可维护、
可按领域扩展,agent 不必每次临时拼查询词。

用法:
  python3 scan_hotspots.py --topics ai,investing,career
"""

import argparse
import json

# 每个领域的查询模板与信源;{date} 由 agent 替换为当天,或直接用「today/本周」
TOPIC_SOURCES = {
    "ai": {
        "label": "AI / Agent 工程",
        "queries": [
            "Hacker News top stories AI agents LLM today",
            "Anthropic OpenAI Google DeepMind announcement this week",
            "GitHub Trending AI agent framework this week",
            "new LLM model release benchmark this week",
        ],
        "fetch": ["https://news.ycombinator.com/",
                  "https://github.com/trending?since=daily"],
    },
    "investing": {
        "label": "投资 / 美股 / 出入金",
        "queries": [
            "US stock market major news today Nasdaq S&P",
            "Fed rate decision earnings this week market moving",
            "长桥 券商 出入金 政策 变化 本周",
        ],
        "fetch": [],
    },
    "career": {
        "label": "职业成长 / 技术人活法",
        "queries": [
            "tech layoffs hiring trends engineer this week",
            "programmer career AI impact discussion this week",
        ],
        "fetch": [],
    },
}


def build_scan_plan(topics):
    """为选定领域拼出扫描计划:每个领域列出查询词和建议 fetch 的信源。"""
    plan = []
    for topic_key in topics:
        source = TOPIC_SOURCES.get(topic_key.strip())
        if not source:
            plan.append({"topic": topic_key, "error": "未知领域,可选 ai/investing/career"})
            continue
        plan.append({
            "topic": topic_key,
            "label": source["label"],
            "web_search_queries": source["queries"],
            "web_fetch_urls": source["fetch"],
        })
    return plan


def main():
    parser = argparse.ArgumentParser(description="热点扫描查询生成器(供 agent 执行搜索)")
    parser.add_argument("--topics", default="ai,investing,career",
                        help="逗号分隔的领域,可选 ai/investing/career")
    args = parser.parse_args()

    plan = build_scan_plan([t for t in args.topics.split(",") if t.strip()])
    output = {
        "note": "以下是扫描建议;agent 需实际调用 WebSearch/WebFetch 抓取,再进第 2 步五重过滤",
        "scan_plan": plan,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
