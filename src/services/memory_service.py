"""
记忆管理服务 — 对话上下文与持久化记忆
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from src.utils.logger import setup_logger
from src.models.schemas import ChatMessage

logger = setup_logger("memory_service")


class MemoryStore:
    """内存存储（可扩展为 Redis / DB）"""

    def __init__(self):
        self._short_term: dict[str, list[ChatMessage]] = {}   # session_id -> messages
        self._long_term: dict[str, Any] = {}                    # key -> value

    def add_message(self, session_id: str, message: ChatMessage):
        """添加消息到短期记忆"""
        if session_id not in self._short_term:
            self._short_term[session_id] = []
        self._short_term[session_id].append(message)
        # 限制上下文窗口大小
        if len(self._short_term[session_id]) > 50:
            self._short_term[session_id] = self._short_term[session_id][-50:]
        logger.debug(f"[Memory] message added to session={session_id}")

    def get_context(self, session_id: str, last_n: Optional[int] = None) -> list[ChatMessage]:
        """获取对话上下文"""
        messages = self._short_term.get(session_id, [])
        if last_n:
            return messages[-last_n:]
        return messages

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
