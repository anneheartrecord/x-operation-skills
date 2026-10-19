"""analyze_x_data.py 纯函数测试:分类、分级、环比切分。"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_x_data import (
    classify_post,
    grade_post,
    compute_period_comparison,
    DEFAULT_CATEGORIES,
)


def test_classify_reply_by_at_prefix():
    """@ 开头视为 reply。"""
    assert classify_post("@someone 回复内容", DEFAULT_CATEGORIES) == "reply"


def test_classify_by_keyword():
    """命中关键词归对应类别。"""
    assert classify_post("今天聊聊美股定投", DEFAULT_CATEGORIES) == "投资"
    assert classify_post("用 claude code 写 agent", DEFAULT_CATEGORIES) == "AI工程"


def test_classify_other_when_no_match():
    """无命中归其他。"""
    assert classify_post("今天天气不错", DEFAULT_CATEGORIES) == "其他"


def test_grade_post_a_high_exposure_high_bookmark():
    """高曝光高收藏 = A。"""
    assert grade_post(impressions=10000, bookmarks=50, median_impressions=1000) == "A"


def test_grade_post_b_low_exposure_high_bookmark():
    """低曝光高收藏 = B(换头重发)。"""
    assert grade_post(impressions=800, bookmarks=10, median_impressions=1000) == "B"


def test_grade_post_c_double_low():
    """双低 = C。"""
    assert grade_post(impressions=100, bookmarks=0, median_impressions=1000) == "C"


def _post(posted_at, views, bookmarks):
    return {"posted_at": posted_at, "views": views, "bookmarks": bookmarks}


def test_period_comparison_splits_by_publish_date():
    """本期(近 7 天)与上期(前 7 天)按发布日正确切分。"""
    today = datetime.date(2026, 7, 14)
    posts = [
        _post("2026-07-12 10:00", 1000, 10),   # 本期
        _post("2026-07-13 10:00", 2000, 20),   # 本期
        _post("2026-07-03 10:00", 500, 5),     # 上期
    ]
    result = compute_period_comparison(posts, window_days=7, today=today, follower_trend=[])
    assert result["current_period"]["posts"] == 2
    assert result["current_period"]["views"] == 3000
    assert result["previous_period"]["posts"] == 1
    assert result["previous_period"]["views"] == 500


def test_period_comparison_follower_delta_none_without_snapshots():
    """快照不足时粉丝环比为 None 且带说明。"""
    today = datetime.date(2026, 7, 14)
    result = compute_period_comparison([], window_days=7, today=today, follower_trend=[])
    assert result["follower_delta"] is None
    assert result["follower_delta_note"]


def _pulse_post(hour, category, views, bookmarks, likes=0, in_window=False):
    return {"hour": hour, "category": category, "views": views,
            "bookmarks": bookmarks, "likes": likes, "in_window": in_window}


def test_build_slot_category_tables_separates_reply():
    """时段表只统计原创;类别表含 reply 单列。"""
    from analyze_x_data import build_slot_category_tables
    posts = [
        _pulse_post(21, "投资", 1000, 10),
        _pulse_post(21, "reply", 500, 1),
    ]
    slot_stats, category_stats = build_slot_category_tables(posts)
    assert slot_stats["20-22"]["posts"] == 1          # reply 不进时段
    assert slot_stats["20-22"]["views"] == 1000
    assert category_stats["reply"]["posts"] == 1      # reply 在类别表单列
    assert category_stats["投资"]["bookmarks"] == 10


def test_quote_repost_candidates_pick_low_views_high_rates():
    """低曝光但收藏比/赞比双高的帖入选;高曝光或低互动的不入选。"""
    from analyze_x_data import find_quote_repost_candidates
    background = [_pulse_post(10, "其他", 1000, 1, likes=1) for _ in range(6)]
    hidden_gem = _pulse_post(21, "投资", 500, 10, likes=8)     # 双高 + 低曝光
    big_hit = _pulse_post(21, "投资", 50000, 100, likes=80)    # 高曝光,不该入选
    low_interaction = _pulse_post(21, "其他", 400, 1, likes=1)  # 绝对量不足
    posts = background + [hidden_gem, big_hit, low_interaction]
    result = find_quote_repost_candidates(posts, median_views=1000)
    texts = [(p["views"], p["bookmarks"]) for p in result]
    assert (500, 10) in texts
    assert (50000, 100) not in texts
    assert (400, 1) not in texts
    assert result[0]["bookmarks_per_10k_views"] == 200.0
