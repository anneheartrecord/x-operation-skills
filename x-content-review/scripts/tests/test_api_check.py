"""fetch_x_api.py 凭证自检纯函数测试(不触网)。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fetch_x_api


def test_missing_credentials_all_absent():
    """全缺 → 返回全部四个 key。"""
    assert set(fetch_x_api.missing_credentials(env={})) == set(fetch_x_api.REQUIRED_ENV_KEYS)


def test_missing_credentials_partial():
    """缺一个 → 只返回缺的那个。"""
    env = {k: "v" for k in fetch_x_api.REQUIRED_ENV_KEYS}
    del env["X_ACCESS_TOKEN"]
    assert fetch_x_api.missing_credentials(env=env) == ["X_ACCESS_TOKEN"]


def test_missing_credentials_none_when_all_present():
    """全有 → 空列表。"""
    env = {k: "v" for k in fetch_x_api.REQUIRED_ENV_KEYS}
    assert fetch_x_api.missing_credentials(env=env) == []


def test_check_credentials_fails_fast_when_missing(monkeypatch):
    """缺变量时 check 直接 FAIL,不触网。"""
    for key in fetch_x_api.REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    ok, message = fetch_x_api.check_credentials()
    assert ok is False
    assert "缺少环境变量" in message
