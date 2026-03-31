"""
错误处理和重试机制 - 统一的异常管理
"""
from __future__ import annotations

import asyncio
import functools
from datetime import datetime
from enum import Enum
from typing import Any, Callable, TypeVar, ParamSpec

from src.utils.logger import setup_logger

logger = setup_logger("errors")

T = TypeVar('T')
P = ParamSpec('P')


class ErrorCode(str, Enum):
    """错误代码枚举"""
    # LLM 相关错误
    LLM_RATE_LIMIT = "LLM_001"
    LLM_TIMEOUT = "LLM_002"
    LLM_CONNECTION = "LLM_003"
    LLM_API_ERROR = "LLM_004"
    LLM_PARSE_ERROR = "LLM_005"

    # Agent 相关错误
    AGENT_INIT_FAILED = "AGENT_001"
    AGENT_EXECUTION_FAILED = "AGENT_002"
    AGENT_INVALID_STATE = "AGENT_003"

    # 状态相关错误
    STATE_INVALID = "STATE_001"
    STATE_MISSING_ARTIFACT = "STATE_002"

    # 配置相关错误
    CONFIG_INVALID = "CONFIG_001"
    CONFIG_MISSING = "CONFIG_002"

    # 通用错误
    UNKNOWN_ERROR = "ERROR_000"


class AppError(Exception):
    """
    应用基础异常类

    所有自定义异常的基类
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class LLMError(AppError):
    """LLM 相关错误"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.LLM_API_ERROR,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message, code, details)
        self.original_error = original_error


class AgentError(AppError):
    """Agent 相关错误"""

    def __init__(
        self,
        message: str,
        agent_name: str,
        code: ErrorCode = ErrorCode.AGENT_EXECUTION_FAILED,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)
        self.agent_name = agent_name


class StateError(AppError):
    """状态相关错误"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.STATE_INVALID,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code, details)


class RetryStrategy:
    """
    重试策略配置
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential: bool = True,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        计算重试延迟

        Args:
            attempt: 当前尝试次数（从 0 开始）

        Returns:
            float: 延迟秒数
        """
        if self.exponential:
            delay = self.base_delay * (2 ** attempt)
        else:
            delay = self.base_delay * (attempt + 1)

        delay = min(delay, self.max_delay)

        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)

        return delay


async def retry_with_strategy(
    coro_func: Callable[P, Callable[..., T]],
    strategy: RetryStrategy | None = None,
    retry_on: tuple[type[Exception], ...] | None = None,
    on_retry: Callable[[int, Exception], Any] | None = None,
) -> Callable[P, T]:
    """
    带重试策略的异步执行

    Args:
        coro_func: 返回协程的函数
        strategy: 重试策略
        retry_on: 需要重试的异常类型
        on_retry: 重试时的回调函数

    Returns:
        包装后的异步函数

    Example:
        async def failing_operation():
            raise ValueError("Failed")

        result = await retry_with_strategy(
            lambda: failing_operation(),
            strategy=RetryStrategy(max_retries=3),
        )
    """
    if strategy is None:
        strategy = RetryStrategy()

    if retry_on is None:
        retry_on = (Exception,)

    last_error = None

    for attempt in range(strategy.max_retries + 1):
        try:
            coro = coro_func()
            return await coro

        except retry_on as e:
            last_error = e

            if attempt >= strategy.max_retries:
                logger.error(
                    f"Retry failed after {strategy.max_retries} attempts: {type(e).__name__}"
                )
                raise

            delay = strategy.get_delay(attempt)

            logger.warning(
                f"Attempt {attempt + 1}/{strategy.max_retries + 1} failed: "
                f"{type(e).__name__}, retrying in {delay:.1f}s"
            )

            if on_retry:
                await on_retry(attempt, e)

            await asyncio.sleep(delay)

    # 理论上不会到达这里
    if last_error:
        raise last_error


def sync_retry_with_strategy(
    func: Callable[P, T],
    strategy: RetryStrategy | None = None,
    retry_on: tuple[type[Exception], ...] | None = None,
) -> Callable[P, T]:
    """
    带重试策略的同步执行（装饰器）

    Args:
        func: 要重试的函数
        strategy: 重试策略
        retry_on: 需要重试的异常类型

    Returns:
        包装后的函数

    Example:
        @sync_retry_with_strategy(strategy=RetryStrategy(max_retries=3))
        def my_function():
            # 可能失败的代码
            pass
    """
    if strategy is None:
        strategy = RetryStrategy()

    if retry_on is None:
        retry_on = (Exception,)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        last_error = None

        for attempt in range(strategy.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except retry_on as e:
                last_error = e

                if attempt >= strategy.max_retries:
                    logger.error(
                        f"Retry failed after {strategy.max_retries} attempts: "
                        f"{type(e).__name__}"
                    )
                    raise

                delay = strategy.get_delay(attempt)

                logger.warning(
                    f"Attempt {attempt + 1}/{strategy.max_retries + 1} failed: "
                    f"{type(e).__name__}, retrying in {delay:.1f}s"
                )

                import time
                time.sleep(delay)

        # 理论上不会到达这里
        if last_error:
            raise last_error

    return wrapper


def async_retry_with_strategy(
    strategy: RetryStrategy | None = None,
    retry_on: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    带重试策略的异步执行装饰器

    Args:
        strategy: 重试策略
        retry_on: 需要重试的异常类型

    Returns:
        装饰器函数

    Example:
        @async_retry_with_strategy(strategy=RetryStrategy(max_retries=3))
        async def my_async_function():
            # 可能失败的异步代码
            pass
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if strategy is None:
                _strategy = RetryStrategy()
            else:
                _strategy = strategy

            if retry_on is None:
                _retry_on = (Exception,)
            else:
                _retry_on = retry_on

            last_error = None

            for attempt in range(_strategy.max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except _retry_on as e:
                    last_error = e

                    if attempt >= _strategy.max_retries:
                        logger.error(
                            f"Retry failed after {_strategy.max_retries} attempts: "
                            f"{type(e).__name__}"
                        )
                        raise

                    delay = _strategy.get_delay(attempt)

                    logger.warning(
                        f"Attempt {attempt + 1}/{_strategy.max_retries + 1} failed: "
                        f"{type(e).__name__}, retrying in {delay:.1f}s"
                    )

                    await asyncio.sleep(delay)

            # 理论上不会到达这里
            if last_error:
                raise last_error

        return wrapper

    return decorator


class ErrorCollector:
    """
    错误收集器

    用于收集和处理多个错误
    """

    def __init__(self):
        self.errors: list[Exception] = []

    def add(self, error: Exception) -> None:
        """添加错误"""
        self.errors.append(error)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def get_all(self) -> list[Exception]:
        """获取所有错误"""
        return self.errors.copy()

    def get_first(self) -> Exception | None:
        """获取第一个错误"""
        return self.errors[0] if self.errors else None

    def clear(self) -> None:
        """清除所有错误"""
        self.errors.clear()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "error_count": len(self.errors),
            "errors": [
                {
                    "type": type(e).__name__,
                    "message": str(e),
                    "code": getattr(e, 'code', None),
                }
                for e in self.errors
            ]
        }


__all__ = [
    "ErrorCode",
    "AppError",
    "LLMError",
    "AgentError",
    "StateError",
    "RetryStrategy",
    "retry_with_strategy",
    "sync_retry_with_strategy",
    "async_retry_with_strategy",
    "ErrorCollector",
]
