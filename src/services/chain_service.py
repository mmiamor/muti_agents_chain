"""
Chain 编排服务 — 自动化任务链的核心
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Callable

from src.utils.logger import setup_logger
from src.models.schemas import ChainConfig, ChainType, TaskResult, TaskStatus

logger = setup_logger("chain_service")


class ChainStep:
    """单步执行单元"""

    def __init__(self, name: str, handler: Callable, **kwargs):
        self.name = name
        self.handler = handler
        self.kwargs = kwargs

    async def execute(self, input_data: Any) -> Any:
        """执行当前步骤"""
        logger.info(f"[Step] {self.name} started")
        result = await self.handler(input_data, **self.kwargs)
        logger.info(f"[Step] {self.name} completed")
        return result


class ChainExecutor:
    """Chain 执行器"""

    def __init__(self, config: ChainConfig):
        self.config = config
        self.steps: list[ChainStep] = []
        self._build_steps()

    def _build_steps(self):
        """根据配置构建步骤列表（可扩展）"""
        # 预留：未来可通过配置动态加载步骤
        pass

    def add_step(self, step: ChainStep):
        """添加步骤"""
        self.steps.append(step)
        return self

    async def run(self, input_data: Any = None) -> TaskResult:
        """执行 Chain"""
        task_id = str(uuid.uuid4())[:8]
        result = TaskResult(task_id=task_id, status=TaskStatus.RUNNING)
        logger.info(f"[Chain:{self.config.name}] started, task_id={task_id}, type={self.config.chain_type}")

        try:
            data = input_data
            chain_type = self.config.chain_type

            if chain_type == ChainType.SEQUENTIAL:
                for step in self.steps:
                    data = await self._run_with_retry(step, data)

            elif chain_type == ChainType.PARALLEL:
                tasks = [self._run_with_retry(step, input_data) for step in self.steps]
                data = await asyncio.gather(*tasks)

            elif chain_type == ChainType.SIMPLE:
                if self.steps:
                    data = await self.steps[0].execute(input_data)

            else:
                # 默认顺序执行
                for step in self.steps:
                    data = await step.execute(data)

            result.status = TaskStatus.SUCCESS
            result.result = data

        except Exception as e:
            logger.error(f"[Chain:{self.config.name}] failed: {e}")
            result.status = TaskStatus.FAILED
            result.error = str(e)

        from datetime import datetime
        result.finished_at = datetime.now()
        logger.info(f"[Chain:{self.config.name}] finished, status={result.status.value}")
        return result

    async def _run_with_retry(self, step: ChainStep, input_data: Any) -> Any:
        """带重试的步骤执行"""
        last_error = None
        for attempt in range(self.config.retry_count + 1):
            try:
                return await step.execute(input_data)
            except Exception as e:
                last_error = e
                logger.warning(f"[Step:{step.name}] attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retry_count:
                    await asyncio.sleep(1 * (attempt + 1))  # 递增等待
        raise last_error
