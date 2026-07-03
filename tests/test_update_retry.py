"""Tests for the transient-failure retry in scripts/update_publicwhip_data._get_json.

A single transient upstream blip (read timeout, dropped connection, or 5xx) once
aborted the entire daily refresh and filed a false-alarm failure issue. These pin
the retry-with-backoff that lets a blip self-heal within the run, while a genuine
sustained outage (or a real 4xx) still fails.
"""
import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import update_publicwhip_data as upd


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    # Don't actually back off during tests.
    monkeypatch.setattr(upd.time, "sleep", lambda *_: None)


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=httpx.Request("GET", "http://x"),
                response=httpx.Response(self.status_code),
            )

    def json(self):
        return self._payload


class _Client:
    """Fake httpx client: `.get` replays a scripted sequence of outcomes.

    Each item is either an Exception (raised) or a _Resp (returned).
    """
    def __init__(self, sequence):
        self._sequence = list(sequence)
        self.calls = 0

    def get(self, url, params=None):
        self.calls += 1
        item = self._sequence.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_retries_transient_timeout_then_succeeds():
    client = _Client([
        httpx.ReadTimeout("read timed out"),
        httpx.ReadTimeout("read timed out"),
        _Resp(payload={"members": 1}),
    ])
    result = upd._get_json(client, "http://x")
    assert result == {"members": 1}
    assert client.calls == 3


def test_retries_5xx_then_succeeds():
    client = _Client([_Resp(status_code=503), _Resp(payload={"ok": True})])
    assert upd._get_json(client, "http://x") == {"ok": True}
    assert client.calls == 2


def test_gives_up_after_attempts_and_reraises():
    client = _Client([httpx.ReadTimeout("t")] * upd.RETRY_ATTEMPTS)
    with pytest.raises(httpx.ReadTimeout):
        upd._get_json(client, "http://x")
    assert client.calls == upd.RETRY_ATTEMPTS  # tried exactly the cap, no infinite loop


def test_4xx_is_not_retried():
    client = _Client([_Resp(status_code=404), _Resp(payload={"unreached": True})])
    with pytest.raises(httpx.HTTPStatusError):
        upd._get_json(client, "http://x")
    assert client.calls == 1  # client error raised immediately, no retry


def test_connection_error_is_retried():
    client = _Client([
        httpx.ConnectError("boom"),
        _Resp(payload={"recovered": True}),
    ])
    assert upd._get_json(client, "http://x") == {"recovered": True}
    assert client.calls == 2
