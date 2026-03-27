"""
任务调度器 — 异步定时任务与后台执行
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Coroutine

from src.utils.logger import setup_logger

logger = setup_logger("scheduler")


class Scheduler:
    """轻量级异步任务调度器"""

    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}

    async def submit(self, name: str, coro: Coroutine, callback: Callable | None = None) -> str:
        """提交一次性任务"""
        async def _wrapped():
            try:
                result = await coro
                if callback:
                    callback(result)
                return result
            except Exception as e:
                logger.error(f"[Scheduler] task '{name}' failed: {e}")
                raise

        task = asyncio.create_task(_wrapped(), name=name)
        self._tasks[name] = task
        logger.info(f"[Scheduler] task '{name}' submitted")
        return name

    async def submit_interval(self, name: str, func: Callable, interval_seconds: float):
        """提交周期性任务"""
        async def _interval():
            while True:
                try:
                    await func()
                except Exception as e:
                    logger.error(f"[Scheduler] interval '{name}' error: {e}")
                await asyncio.sleep(interval_seconds)

        task = asyncio.create_task(_interval(), name=name)
        self._tasks[name] = task
        logger.info(f"[Scheduler] interval '{name}' started (every {interval_seconds}s)")

    def cancel(self, name: str):
        """取消任务"""
        task = self._tasks.pop(name, None)
        if task and not task.done():
            task.cancel()
            logger.info(f"[Scheduler] task '{name}' cancelled")

    def status(self) -> dict[str, str]:
        """查看所有任务状态"""
        return {name: ("running" if not t.done() else "done") for name, t in self._tasks.items()}


scheduler = Scheduler()
