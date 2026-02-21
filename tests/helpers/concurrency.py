"""
Helpers for writing concurrency and async-polling tests.
"""

import asyncio
from typing import Any, Callable


async def run_concurrent(func: Callable, n: int = 10) -> list[Any]:
    """Run async ``func()`` n times concurrently; return results (exceptions included)."""
    tasks = [asyncio.create_task(func()) for _ in range(n)]
    return await asyncio.gather(*tasks, return_exceptions=True)


async def assert_eventually(
    condition: Callable[[], bool],
    timeout: float = 2.0,
    interval: float = 0.05,
    msg: str = "Condition not met",
) -> None:
    """Poll ``condition()`` until it returns True or ``timeout`` elapses."""
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        if condition():
            return
        await asyncio.sleep(interval)
    raise AssertionError(f"{msg} (waited {timeout}s)")
