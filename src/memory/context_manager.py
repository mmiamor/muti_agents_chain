"""
上下文记忆管理 — 智能压缩与优化
- 自动检测上下文长度并触发压缩
- 保留关键信息（用户需求、决策、重要反馈）
- 滑动窗口 + 语义压缩相结合
"""
from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

logger = logging.getLogger("context_manager")


@dataclass
class ContextConfig:
    """上下文管理配置"""
    max_messages: int = 100              # 最大消息数量
    max_tokens: int = 8000               # 最大 token 估算（保守估计）
    compact_threshold: float = 0.8       # 触发压缩阈值（80%）
    keep_first_n: int = 5                # 保留前 N 条重要消息
    keep_last_n: int = 20                # 保留最近 N 条消息
    enable_semantic_compact: bool = True # 启用语义压缩


@dataclass
class ContextStats:
    """上下文统计"""
    total_messages: int = 0
    total_estimated_tokens: int = 0
    compression_count: int = 0
    last_compaction_ratio: float = 0.0


class ContextManager:
    """
    智能上下文管理器

    功能：
    1. 自动检测上下文长度
    2. 多级压缩策略：滑动窗口 → 语义摘要
    3. 保留关键消息（用户需求、决策点、重要反馈）
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()
        self.stats = ContextStats()
        self._critical_keywords = [
            "需求", "vision", "目标", "必须", "关键",
            "decision", "requirement", "must", "critical",
            "反馈", "review", "approval", "approved"
        ]

    def estimate_tokens(self, messages: list[BaseMessage]) -> int:
        """估算消息列表的 token 数（粗略估计：中文≈2字符/token，英文≈4字符/token）"""
        total_chars = sum(len(m.content) for m in messages)
        # 混合估算：平均 3 字符/token
        return int(total_chars / 3)

    def should_compact(self, messages: list[BaseMessage]) -> bool:
        """判断是否需要压缩"""
        msg_count = len(messages)
        token_estimate = self.estimate_tokens(messages)

        self.stats.total_messages = msg_count
        self.stats.total_estimated_tokens = token_estimate

        # 触发条件：消息数量 OR token 估算超过阈值
        return (
            msg_count >= self.config.max_messages * self.config.compact_threshold
            or token_estimate >= self.config.max_tokens * self.config.compact_threshold
        )

    def compact_messages(
        self,
        messages: list[BaseMessage],
        agent_name: Optional[str] = None,
    ) -> list[BaseMessage]:
        """
        智能压缩消息列表

        策略：
        1. 保留系统提示
        2. 保留前 N 条关键消息（通常包含初始需求）
        3. 保留最近 N 条消息（维持对话连贯性）
        4. 中间部分摘要压缩
        """
        if not messages:
            return messages

        original_count = len(messages)
        logger.info(
            f"[ContextManager] 开始压缩上下文: {original_count} 条消息, "
            f"估算 {self.estimate_tokens(messages)} tokens"
        )

        # 分离系统消息
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        other_messages = [m for m in messages if not isinstance(m, SystemMessage)]

        if len(other_messages) <= self.config.keep_first_n + self.config.keep_last_n:
            # 消息不多，无需压缩
            return messages

        # 提取关键消息
        critical_messages = self._extract_critical_messages(
            other_messages[:len(other_messages) // 2]  # 从前半部分提取
        )

        # 保留最近的消息
        recent_messages = other_messages[-self.config.keep_last_n:]

        # 构建压缩后的消息列表
        compacted = system_messages + critical_messages + recent_messages

        # 如果启用了语义压缩，生成中间摘要
        if self.config.enable_semantic_compact:
            middle_messages = (
                other_messages[
                    self.config.keep_first_n :
                    -self.config.keep_last_n
                ]
            )
            if middle_messages:
                summary = self._generate_summary(middle_messages, agent_name)
                if summary:
                    compacted.insert(
                        len(system_messages) + len(critical_messages),
                        SystemMessage(content=summary)
                    )

        compression_ratio = 1 - (len(compacted) / original_count)
        self.stats.compression_count += 1
        self.stats.last_compaction_ratio = compression_ratio

        logger.info(
            f"[ContextManager] 压缩完成: {original_count} → {len(compacted)} "
            f"(压缩率 {compression_ratio:.1%})"
        )

        return compacted

    def _extract_critical_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """提取包含关键信息的消息"""
        critical = []

        for msg in messages[:self.config.keep_first_n]:
            content_lower = msg.content.lower()
            # 检查是否包含关键词
            if any(keyword in content_lower for keyword in self._critical_keywords):
                critical.append(msg)
            elif isinstance(msg, HumanMessage):
                # 用户消息通常比较重要
                critical.append(msg)

        return critical

    def _generate_summary(
        self,
        messages: list[BaseMessage],
        agent_name: Optional[str] = None,
    ) -> str:
        """
        生成中间消息的摘要

        在实际使用中，可以调用 LLM 生成更智能的摘要
        这里使用简单的启发式方法
        """
        if not messages:
            return ""

        # 统计 Agent 活跃度
        agent_activities = Counter()
        for msg in messages:
            if hasattr(msg, 'name') and msg.name:
                agent_activities[msg.name] += 1
            elif isinstance(msg, AIMessage):
                agent_activities[agent_name or "assistant"] += 1

        # 构建简单摘要
        summary_parts = [
            "## 对话历史摘要\n\n",
            f"中间经过了 {len(messages)} 条消息的交互，",
        ]

        if agent_activities:
            top_agents = agent_activities.most_common(3)
            agents_str = "、".join([f"{agent}({count}次)" for agent, count in top_agents])
            summary_parts.append(f"主要参与者：{agents_str}。")

        summary_parts.append("\n\n关键讨论内容已保留在前后消息中。")

        return "".join(summary_parts)

    def add_system_context(
        self,
        messages: list[BaseMessage],
        system_prompt: str,
    ) -> list[BaseMessage]:
        """添加或更新系统提示"""
        # 移除旧的系统消息
        filtered = [m for m in messages if not isinstance(m, SystemMessage)]
        # 添加新的系统消息
        return [SystemMessage(content=system_prompt)] + filtered

    def get_context_for_prompt(
        self,
        messages: list[BaseMessage],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> list[BaseMessage]:
        """
        为 LLM 提示准备优化的上下文

        Args:
            messages: 原始消息列表
            system_prompt: 系统提示（可选）
            max_tokens: 本次请求的最大 token 限制（可选）

        Returns:
            优化后的消息列表
        """
        context = messages.copy()

        # 添加系统提示
        if system_prompt:
            context = self.add_system_context(context, system_prompt)

        # 检查是否需要压缩
        if self.should_compact(context):
            context = self.compact_messages(context)

        # 如果指定了 token 限制，进一步裁剪
        if max_tokens:
            context = self._trim_to_tokens(context, max_tokens)

        return context

    def _trim_to_tokens(
        self,
        messages: list[BaseMessage],
        max_tokens: int,
    ) -> list[BaseMessage]:
        """根据 token 限制裁剪消息（保留系统消息和最近的消息）"""
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        other_messages = [m for m in messages if not isinstance(m, SystemMessage)]

        result = system_messages.copy()
        current_tokens = self.estimate_tokens(system_messages)

        for msg in reversed(other_messages):
            msg_tokens = len(msg.content) / 3  # 粗略估计
            if current_tokens + msg_tokens <= max_tokens:
                result.insert(len(system_messages), msg)
                current_tokens += msg_tokens
            else:
                break

        return result

    def get_stats(self) -> dict[str, Any]:
        """获取上下文管理统计信息"""
        return {
            "total_messages": self.stats.total_messages,
            "estimated_tokens": self.stats.total_estimated_tokens,
            "compression_count": self.stats.compression_count,
            "last_compaction_ratio": self.stats.last_compaction_ratio,
        }


# ── 全局单例 ─────────────────────────────────────

_default_context_manager: Optional[ContextManager] = None


def get_context_manager(config: Optional[ContextConfig] = None) -> ContextManager:
    """获取全局上下文管理器"""
    global _default_context_manager
    if _default_context_manager is None or config is not None:
        _default_context_manager = ContextManager(config)
    return _default_context_manager
