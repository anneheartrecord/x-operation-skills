"""split_thread.py 纯函数测试:加权长度、句界拆分、链接归末条、费用估算。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from split_thread import weighted_len, pack_segments, build_thread, _hard_cut


def test_weighted_len_cjk_counts_two():
    """中文/全角算 2,ASCII 算 1。"""
    assert weighted_len("abc") == 3
    assert weighted_len("中文") == 4
    assert weighted_len("a中") == 3


def test_pack_segments_splits_long_chinese_at_sentence_boundary():
    """超 270 加权的中文按句界拆成多条,每条 ≤270。"""
    sentence = "这是一句测试文本。" * 40  # 远超 270 加权
    segments = pack_segments(sentence, 270)
    assert len(segments) > 1
    assert all(weighted_len(seg) <= 270 for seg in segments)


def test_pack_segments_keeps_short_text_single():
    """短文本不拆。"""
    segments = pack_segments("一句话。", 270)
    assert len(segments) == 1


def test_hard_cut_respects_limit():
    """超长无标点单句硬切不超限。"""
    long_run = "很长的一段没有标点的中文" * 30
    cut = _hard_cut(long_run, 270)
    assert weighted_len(cut) <= 270
    assert len(cut) > 0


def test_build_thread_pools_links_into_last_reply():
    """链接被抽到末条自回复,正文各条不含链接。"""
    text = "第一段观点。\n\n第二段观点,仓库在 https://github.com/a/b 也参考了 https://x.com/c。"
    plan = build_thread(text, 270, number=False)
    link_tweets = [t for t in plan["tweets"] if t["has_link"]]
    assert len(link_tweets) == 1
    assert link_tweets[0] is plan["tweets"][-1]  # 链接在最后一条
    # 正文条不含 http
    for tweet in plan["tweets"][:-1]:
        assert "http" not in tweet["text"]


def test_build_thread_cost_estimate():
    """费用 = 链接条 $0.20 + 正文条各 $0.015。"""
    text = "观点一。\n\n观点二,见 https://example.com/x。"
    plan = build_thread(text, 270, number=False)
    text_tweets = plan["tweet_count"] - plan["link_tweets"]
    expected = round(plan["link_tweets"] * 0.20 + text_tweets * 0.015, 3)
    assert plan["estimated_cost_usd"] == expected
    assert plan["link_tweets"] == 1


def test_build_thread_no_links_no_premium():
    """无链接时不产生 $0.20 溢价条。"""
    plan = build_thread("纯文字观点,没有任何链接。", 270, number=False)
    assert plan["link_tweets"] == 0
    assert all(not t["has_link"] for t in plan["tweets"])


def test_build_thread_numbering():
    """--number 给多条加 i/n 编号。"""
    text = "这是一句测试文本。" * 40
    plan = build_thread(text, 270, number=True)
    if plan["tweet_count"] > 1:
        assert "/" in plan["tweets"][0]["text"]
