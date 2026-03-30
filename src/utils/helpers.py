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


def message_to_dict(message: Any) -> dict:
    """将LangChain消息转换为字典"""
    result = {
        "content": message.content,
        "role": getattr(message, "type", "unknown"),
    }

    # 添加name字段（如果有）
    if hasattr(message, "name") and message.name:
        result["name"] = message.name

    return result


def get_revision_count(state: dict, agent_name: str) -> int:
    """获取Agent的修订次数"""
    revision_counts = state.get("revision_counts", {})
    return revision_counts.get(agent_name, 0)


def next_revision_count(state: dict, agent_name: str) -> dict:
    """增加修订次数并返回更新"""
    revision_counts = state.get("revision_counts", {})
    revision_counts[agent_name] = revision_counts.get(agent_name, 0) + 1
    return {"revision_counts": revision_counts}
