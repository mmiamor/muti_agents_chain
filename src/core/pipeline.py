"""
处理管道 — 输入预处理 → 主处理 → 输出后处理
"""
from __future__ import annotations

from typing import Any, Callable

from src.utils.logger import setup_logger

logger = setup_logger("pipeline")


class Pipeline:
    """数据处理管道"""

    def __init__(self, name: str = "default"):
        self.name = name
        self._pre_processors: list[Callable] = []
        self._processor: Callable | None = None
        self._post_processors: list[Callable] = []

    def pre_process(self, func: Callable) -> "Pipeline":
        """添加预处理步骤"""
        self._pre_processors.append(func)
        return self

    def process(self, func: Callable) -> "Pipeline":
        """设置主处理函数"""
        self._processor = func
        return self

    def post_process(self, func: Callable) -> "Pipeline":
        """添加后处理步骤"""
        self._post_processors.append(func)
        return self

    async def execute(self, input_data: Any) -> Any:
        """执行完整管道"""
        logger.info(f"[Pipeline:{self.name}] execute started")

        # 预处理
        data = input_data
        for step in self._pre_processors:
            if asyncio.iscoroutinefunction(step):
                data = await step(data)
            else:
                data = step(data)

        # 主处理
        if self._processor:
            if asyncio.iscoroutinefunction(self._processor):
                data = await self._processor(data)
            else:
                data = self._processor(data)

        # 后处理
        for step in self._post_processors:
            if asyncio.iscoroutinefunction(step):
                data = await step(data)
            else:
                data = step(data)

        logger.info(f"[Pipeline:{self.name}] execute completed")
        return data
