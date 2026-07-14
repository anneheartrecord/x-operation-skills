"""pulse_to_dashboard.py 测试:渲染 + 标记段替换(不触网、不碰真看板)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse_to_dashboard import (
    render_follower_trend,
    render_analysis,
    build_block,
    write_block,
    MARK_START,
    MARK_END,
)


def test_follower_trend_empty():
    """无快照 → 提示暂无。"""
    assert "暂无快照" in render_follower_trend([])


def test_follower_trend_weekly_delta():
    """跨 7 天的快照 → 算出近 7 天涨粉。"""
    snaps = [
        {"date": "2026-07-01", "followers": 3600},
        {"date": "2026-07-08", "followers": 3629},
    ]
    out = render_follower_trend(snaps)
    assert "3629" in out
    assert "+29" in out


def test_follower_trend_insufficient_span():
    """跨度不足 7 天 → 标注跨度而非编造环比。"""
    snaps = [
        {"date": "2026-07-13", "followers": 3626},
        {"date": "2026-07-14", "followers": 3629},
    ]
    out = render_follower_trend(snaps)
    assert "3629" in out
    assert "跨度" in out


def test_render_analysis_categories_and_comparison():
    """分析 JSON → 环比行 + 类别表。"""
    analysis = {"content": {
        "period_comparison": {
            "current_period": {"posts": 26, "views": 77000, "bookmarks_per_10k_views": 44.2},
            "previous_period": {"posts": 21, "views": 115000, "bookmarks_per_10k_views": 45.1},
        },
        "categories": [
            {"category": "投资", "posts": 29, "bookmarks_per_10k_views": 39.6},
            {"category": "AI工程", "posts": 68, "bookmarks_per_10k_views": 14.0},
        ],
        "time_slots_beijing": [
            {"slot_beijing": "14-16", "posts": 20, "bookmarks_per_10k_views": 67.4},
        ],
        "repost_candidates_grade_b": [],
    }}
    blocks = "\n".join(render_analysis(analysis))
    assert "本期 vs 上期" in blocks
    assert "投资" in blocks and "39.6" in blocks
    assert "14-16" in blocks


def test_render_analysis_empty():
    """无 content → 提示暂无。"""
    assert "暂无" in render_analysis({})[0]


def test_write_block_replaces_only_marked_section(tmp_path):
    """只替换标记段,标记外内容原样保留。"""
    dashboard = tmp_path / "dash.md"
    dashboard.write_text(
        f"# 看板\n\n前面内容\n\n{MARK_START}\n旧数据\n{MARK_END}\n\n后面内容\n",
        encoding="utf-8")
    block = build_block([{"date": "2026-07-14", "followers": 3629}], {}, "2026-07-14 10:00")
    assert write_block(str(dashboard), block) is True
    result = dashboard.read_text(encoding="utf-8")
    assert "前面内容" in result and "后面内容" in result  # 标记外不动
    assert "旧数据" not in result                          # 旧内容被换掉
    assert "3629" in result                               # 新数据写入


def test_write_block_skips_when_no_markers(tmp_path):
    """看板缺标记 → 安全跳过,不破坏文件。"""
    dashboard = tmp_path / "dash.md"
    dashboard.write_text("# 看板\n\n没有标记\n", encoding="utf-8")
    block = build_block([], {}, "t")
    assert write_block(str(dashboard), block) is False
    assert dashboard.read_text(encoding="utf-8") == "# 看板\n\n没有标记\n"
