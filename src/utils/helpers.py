"""
通用工具函数
"""
from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable, Coroutine


def async_wrapper(func: Callable) -> Coroutine:
    """将同步函数包装为异步调用（在线程池中执行）"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    return wrapper


def truncate(text: str, max_len: int = 200) -> str:
    """截断文本"""
    return text[:max_len] + "..." if len(text) > max_len else text


def safe_get(data: dict, keys: list[str], default: Any = None) -> Any:
    """安全获取嵌套字典值"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data
