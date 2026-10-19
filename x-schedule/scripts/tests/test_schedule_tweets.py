"""schedule_tweets.py 纯函数测试:计长、frontmatter 剥离、排期分配、payload。"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schedule_tweets import (
    TZ_BEIJING,
    build_create_payload,
    build_plan,
    strip_frontmatter,
    weighted_len,
)


def test_weighted_len_cjk_counts_double():
    """中文算 2,ASCII 算 1。"""
    assert weighted_len("ab") == 2
    assert weighted_len("中文") == 4


def test_weighted_len_url_counts_as_tco():
    """URL 无论多长按 t.co 的 23 计。"""
    long_url = "https://example.com/very/long/path?with=query&and=more"
    assert weighted_len(long_url) == 23
    assert weighted_len(f"看这个 {long_url}") == 6 + 1 + 23


def test_strip_frontmatter_removes_yaml_header():
    """YAML frontmatter 被剥掉,只留正文。"""
    text = "---\ntype: 成稿\nstatus: draft\n---\n正文第一行"
    assert strip_frontmatter(text) == "正文第一行"


def test_strip_frontmatter_keeps_plain_text():
    """没有 frontmatter 的文本原样返回。"""
    assert strip_frontmatter("直接正文") == "直接正文"


def _draft(name):
    return {"name": name, "text": "内容", "weighted_len": 4, "over_limit": False}


def test_build_plan_skips_past_slots_and_rolls_over():
    """已过去的时段被跳过;一天排满自动进下一天。"""
    # now = 12:30,今天 11 点已过 → 第一条排 14 点
    now = datetime.datetime(2026, 7, 21, 12, 30, tzinfo=TZ_BEIJING)
    plan = build_plan([_draft("a"), _draft("b"), _draft("c"), _draft("d")],
                      now, slots=(11, 14, 20, 23))
    assert [item["scheduled_at"] for item in plan] == [
        "2026-07-21 14:00", "2026-07-21 20:00", "2026-07-21 23:00",
        "2026-07-22 11:00"]


def test_build_plan_respects_margin():
    """距 now 不足 margin 的时段不用(10:55 排不进 11:00)。"""
    now = datetime.datetime(2026, 7, 21, 10, 55, tzinfo=TZ_BEIJING)
    plan = build_plan([_draft("a")], now, slots=(11, 14, 20, 23))
    assert plan[0]["scheduled_at"] == "2026-07-21 14:00"


def test_build_plan_start_date_in_future():
    """指定未来起始日时,从该日第一个时段开始排。"""
    now = datetime.datetime(2026, 7, 21, 22, 0, tzinfo=TZ_BEIJING)
    plan = build_plan([_draft("a")], now, slots=(11, 14, 20, 23),
                      start_date=datetime.date(2026, 7, 23))
    assert plan[0]["scheduled_at"] == "2026-07-23 11:00"


def test_build_create_payload_shape():
    """payload 含正文、执行时间与 queryId。"""
    payload = build_create_payload("hello", 1790000000)
    assert payload["variables"]["post_tweet_request"]["status"] == "hello"
    assert payload["variables"]["execute_at"] == 1790000000
    assert payload["queryId"]
