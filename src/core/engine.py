"""
核心引擎 — 贯穿 LLM / Chain / Memory 的调度中心
"""
from __future__ import annotations

from src.config import settings
from src.utils.logger import setup_logger
from src.services.llm_service import LLMService
from src.services.chain_service import ChainExecutor, ChainConfig
from src.services.memory_service import MemoryStore
from src.models.schemas import ChatMessage, ChainType

logger = setup_logger("engine")


class Engine:
    """AI 后台主引擎"""

    def __init__(self):
        self.llm = LLMService(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            default_model=settings.DEFAULT_MODEL,
        )
        self.memory = MemoryStore()

    async def chat(self, session_id: str, prompt: str, system: str | None = None) -> str:
        """带记忆的聊天"""
        # 构建上下文
        messages = []
        context = self.memory.get_context(session_id, last_n=20)

        if system:
            messages.append(ChatMessage(role="system", content=system))
        messages.extend(context)
        messages.append(ChatMessage(role="user", content=prompt))

        # 调用 LLM
        from src.models.schemas import LLMRequest
        request = LLMRequest(model=settings.DEFAULT_MODEL, messages=messages)
        response = await self.llm.chat(request)

        # 保存记忆
        self.memory.add_message(session_id, ChatMessage(role="user", content=prompt))
        self.memory.add_message(session_id, ChatMessage(role="assistant", content=response.content))

        return response.content

    def create_chain(self, name: str, chain_type: ChainType = ChainType.SEQUENTIAL) -> ChainExecutor:
        """创建执行链"""
        config = ChainConfig(name=name, chain_type=chain_type)
        return ChainExecutor(config)

    async def health_check(self) -> dict:
        """健康检查"""
        return {"status": "ok", "model": settings.DEFAULT_MODEL}


# 全局引擎单例
engine = Engine()
