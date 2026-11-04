import asyncio

import pytest

import config.database as database_module


def test_connect_retries_stalled_attempts_with_short_timeout(monkeypatch):
    timeouts = []

    async def fake_connect(*_args, timeout):
        timeouts.append(timeout)
        if len(timeouts) < 3:
            raise TimeoutError
        return "connection"

    monkeypatch.setattr(database_module.asyncpg, "connect", fake_connect)
    result = asyncio.run(database_module._connect_with_retry("dsn", timeout=60))
    assert result == "connection"
    assert timeouts == [10, 10, 10]


def test_connect_gives_up_after_last_attempt(monkeypatch):
    calls = []

    async def fake_connect(*_args, timeout):
        calls.append(timeout)
        raise TimeoutError

    monkeypatch.setattr(database_module.asyncpg, "connect", fake_connect)
    with pytest.raises(TimeoutError):
        asyncio.run(database_module._connect_with_retry("dsn", timeout=60))
    assert len(calls) == 6
