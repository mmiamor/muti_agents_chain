"""
Agent 上下文优化工具 - 简化 Agent 使用优化上下文的代码
"""
from __future__ import annotations

from typing import Optional

from langchain_core.messages import BaseMessage

from src.memory.context_manager import get_context_manager


def prepare_messages_for_llm(
    state_messages: list[BaseMessage],
    system_prompt: str,
    agent_name: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> list[dict[str, str]]:
    """
    为 LLM 调用准备优化的消息列表

    这是 Agent 节点中的主要入口函数，自动处理：
    1. 上下文压缩
    2. 系统提示添加
    3. Token 限制裁剪

    Args:
        state_messages: LangGraph State 中的消息列表
        system_prompt: Agent 的系统提示词
        agent_name: 当前 Agent 名称（用于日志）
        max_tokens: 最大 token 限制

    Returns:
        适合 LLM SDK 使用的消息列表（dict 格式）

    Example:
        >>> messages = prepare_messages_for_llm(
        ...     state["messages"],
        ...     SYSTEM_PROMPT,
        ...     agent_name="pm_agent"
        ... )
        >>> response = await client.chat.completions.create(
        ...     messages=messages,
        ...     model="glm-5"
        ... )
    """
    context_manager = get_context_manager()

    # 使用上下文管理器优化
    optimized = context_manager.get_context_for_prompt(
        state_messages,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
    )

    # 转换为 OpenAI SDK 格式
    role_map = {
        "system": "system",
        "human": "user",
        "ai": "assistant",
        "tool": "tool",
    }

    return [
        {"role": role_map.get(msg.type, msg.type), "content": msg.content}
        for msg in optimized
    ]


def estimate_context_tokens(messages: list[BaseMessage]) -> int:
    """估算上下文的 token 数量"""
    context_manager = get_context_manager()
    return context_manager.estimate_tokens(messages)


def should_compact_context(messages: list[BaseMessage]) -> bool:
    """检查是否需要压缩上下文"""
    context_manager = get_context_manager()
    return context_manager.should_compact(messages)


def get_context_stats() -> dict:
    """获取上下文管理统计信息"""
    context_manager = get_context_manager()
    return context_manager.get_stats()
