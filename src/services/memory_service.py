"""
记忆管理服务 — 对话上下文与持久化记忆（集成智能压缩）
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from langchain_core.messages import BaseMessage

from src.memory.context_manager import ContextManager, get_context_manager, ContextConfig
from src.utils.logger import setup_logger
from src.models.schemas import ChatMessage

logger = setup_logger("memory_service")


class MemoryStore:
    """内存存储（可扩展为 Redis / DB）"""

    def __init__(self, enable_context_management: bool = True):
        self._short_term: dict[str, list[ChatMessage]] = {}   # session_id -> messages
        self._long_term: dict[str, Any] = {}                    # key -> value

        # 智能上下文管理
        self._context_manager: Optional[ContextManager] = None
        if enable_context_management:
            self._context_manager = get_context_manager()
            logger.info("[MemoryStore] 智能上下文管理已启用")

    def add_message(self, session_id: str, message: ChatMessage):
        """添加消息到短期记忆"""
        if session_id not in self._short_term:
            self._short_term[session_id] = []
        self._short_term[session_id].append(message)

        # 使用上下文管理器进行智能压缩
        if self._context_manager:
            messages = self._short_term[session_id]
            if self._context_manager.should_compact(
                [self._chat_msg_to_base_msg(m) for m in messages]
            ):
                # 转换为 BaseMessage 进行压缩
                base_messages = [self._chat_msg_to_base_msg(m) for m in messages]
                compacted = self._context_manager.compact_messages(base_messages)
                # 转换回 ChatMessage
                self._short_term[session_id] = [
                    self._base_msg_to_chat_msg(m) for m in compacted
                ]
                logger.debug(
                    f"[Memory] session={session_id} 上下文已压缩, "
                    f"当前消息数: {len(self._short_term[session_id])}"
                )
        else:
            # 传统的简单限制
            if len(self._short_term[session_id]) > 50:
                self._short_term[session_id] = self._short_term[session_id][-50:]

        logger.debug(f"[Memory] message added to session={session_id}")

    def get_context(
        self,
        session_id: str,
        last_n: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ) -> list[ChatMessage]:
        """
        获取对话上下文（支持智能裁剪）

        Args:
            session_id: 会话ID
            last_n: 仅获取最近 N 条消息
            max_tokens: 最大 token 限制（触发智能裁剪）

        Returns:
            优化后的消息列表
        """
        messages = self._short_term.get(session_id, [])

        if self._context_manager and max_tokens:
            # 使用上下文管理器进行智能裁剪
            base_messages = [self._chat_msg_to_base_msg(m) for m in messages]
            trimmed = self._context_manager._trim_to_tokens(base_messages, max_tokens)
            return [self._base_msg_to_chat_msg(m) for m in trimmed]

        if last_n:
            return messages[-last_n:]
        return messages

    def get_optimized_context(
        self,
        session_id: str,
        system_prompt: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> list[BaseMessage]:
        """
        为 Agent 准备优化的上下文

        Args:
            session_id: 会话ID
            system_prompt: 系统提示（Agent 的角色定义）
            agent_name: 当前 Agent 名称

        Returns:
            优化后的 LangChain BaseMessage 列表
        """
        chat_messages = self._short_term.get(session_id, [])
        base_messages = [self._chat_msg_to_base_msg(m) for m in chat_messages]

        if self._context_manager:
            return self._context_manager.get_context_for_prompt(
                base_messages,
                system_prompt=system_prompt,
            )

        # 简单模式：直接添加系统提示
        if system_prompt:
            from langchain_core.messages import SystemMessage
            return [SystemMessage(content=system_prompt)] + base_messages

        return base_messages

    def get_context_stats(self, session_id: str) -> dict[str, Any]:
        """获取会话上下文统计信息"""
        messages = self._short_term.get(session_id, [])
        stats = {
            "session_id": session_id,
            "message_count": len(messages),
            "estimated_tokens": sum(len(m.content) for m in messages) // 3,
        }

        if self._context_manager:
            stats.update(self._context_manager.get_stats())

        return stats

    def clear_session(self, session_id: str):
        """清除会话记忆"""
        self._short_term.pop(session_id, None)
        logger.info(f"[Memory] session={session_id} cleared")

    def save(self, key: str, value: Any):
        """保存到长期记忆"""
        self._long_term[key] = value
        logger.debug(f"[Memory] saved key={key}")

    def load(self, key: str, default: Any = None) -> Any:
        """从长期记忆读取"""
        return self._long_term.get(key, default)

    def delete(self, key: str):
        """删除长期记忆"""
        self._long_term.pop(key, None)

    @staticmethod
    def _chat_msg_to_base_msg(msg: ChatMessage) -> BaseMessage:
        """转换 ChatMessage 到 LangChain BaseMessage"""
        from langchain_core.messages import (
            HumanMessage,
            AIMessage,
            SystemMessage,
            ToolMessage,
        )

        content = msg.content
        if msg.role == "system":
            return SystemMessage(content=content)
        elif msg.role == "user":
            return HumanMessage(content=content)
        elif msg.role == "assistant":
            return AIMessage(content=content)
        elif msg.role == "tool":
            return ToolMessage(content=content, tool_call_id="")
        else:
            return HumanMessage(content=content)

    @staticmethod
    def _base_msg_to_chat_msg(msg: BaseMessage) -> ChatMessage:
        """转换 LangChain BaseMessage 到 ChatMessage"""
        role_mapping = {
            "system": "system",
            "human": "user",
            "ai": "assistant",
            "tool": "tool",
        }
        role = role_mapping.get(msg.type, "user")
        return ChatMessage(role=role, content=msg.content)
