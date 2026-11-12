"""Timed sweeps run once across workers (audit C2): a second holder skips."""

import asyncio

import pytest

from api.main import _exclusively


@pytest.mark.asyncio
async def test_a_sweep_already_running_elsewhere_is_skipped():
    started, release = asyncio.Event(), asyncio.Event()
    runs = []

    async def slow():
        runs.append("first")
        started.set()
        await release.wait()

    async def quick():
        runs.append("second")

    first = asyncio.create_task(_exclusively(4242, slow))
    await started.wait()
    assert await _exclusively(4242, quick) is False  # lock held by the first
    release.set()
    assert await first is True
    assert await _exclusively(4242, quick) is True  # released after the sweep
    assert runs == ["first", "second"]
