"""fetch_x_pulse.py 作者过滤/去重纯函数测试(不触网)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetch_x_pulse import is_own_unseen_post


def test_keeps_own_post():
    """作者是本人且未见过 → 保留。"""
    seen = set()
    assert is_own_unseen_post("Charles77xixi", "Charles77xixi", "111", seen) is True
    assert "111" in seen


def test_case_insensitive_author_match():
    """作者匹配大小写不敏感。"""
    assert is_own_unseen_post("charles77xixi", "Charles77xixi", "1", set()) is True


def test_drops_retweet_of_other_author():
    """转推(原作者非本人)被剔除 —— 防百万曝光官方号内容污染。"""
    assert is_own_unseen_post("claudeai", "Charles77xixi", "222", set()) is False


def test_drops_empty_author():
    """作者为空 → 剔除。"""
    assert is_own_unseen_post("", "Charles77xixi", "333", set()) is False


def test_dedup_same_id():
    """同 id 第二次出现 → 去重剔除。"""
    seen = {"444"}
    assert is_own_unseen_post("Charles77xixi", "Charles77xixi", "444", seen) is False
