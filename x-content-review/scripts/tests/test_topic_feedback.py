"""topic_feedback.py 测试:复盘结论 → 选题回环 markdown。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topic_feedback import build_markdown


def _analysis(categories=None, top=None, repost=None):
    return {
        "generated_at": "2026-07-14 10:00",
        "content": {
            "categories": categories or [],
            "window_top_posts": top or [],
            "repost_candidates_grade_b": repost or [],
        },
    }


def test_a_grade_posts_become_series_block():
    """A 级帖进「扩成系列」块。"""
    analysis = _analysis(top=[
        {"grade": "A", "views": 55000, "bookmarks": 528, "text": "开港美股券商五家亲测", "url": "u1"},
    ])
    md = build_markdown(analysis)
    assert "扩成系列" in md
    assert "开港美股券商五家亲测" in md


def test_b_grade_posts_become_repost_queue():
    """B 级帖进「换头重发」队列。"""
    analysis = _analysis(repost=[
        {"views": 800, "bookmarks": 9, "text": "花时间生产而不是消费", "url": "u2"},
    ])
    md = build_markdown(analysis)
    assert "换头重发" in md
    assert "花时间生产而不是消费" in md


def test_category_production_advice():
    """高效类别标 ⬆️,垫底标 ⬇️。"""
    analysis = _analysis(categories=[
        {"category": "投资", "posts": 29, "bookmarks_per_10k_views": 39.6},
        {"category": "其他", "posts": 109, "bookmarks_per_10k_views": 6.9},
    ])
    md = build_markdown(analysis)
    assert "投资" in md and "其他" in md
    assert "⬆️" in md and "⬇️" in md


def test_empty_analysis_says_nothing_to_loop():
    """无 A/B/足量类别时给出提示而非空输出。"""
    md = build_markdown(_analysis())
    assert "没有可回环" in md
