"""
API 路由定义
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from src.api.server import app
from src.core.engine import engine
from src.models.schemas import ChatMessage, LLMRequest, LLMResponse

router = APIRouter(prefix="/api/v1", tags=["v1"])


# ── 健康检查 ──

@router.get("/health")
async def health():
    return await engine.health_check()


# ── 聊天接口 ──

@router.post("/chat", response_model=LLMResponse)
async def chat(request: LLMRequest):
    """直接调用 LLM（无记忆）"""
    try:
        return await engine.llm.chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 带记忆的会话 ──

@router.post("/session/{session_id}/chat")
async def session_chat(session_id: str, prompt: str, system: str | None = None):
    """带上下文记忆的对话"""
    try:
        result = await engine.chat(session_id, prompt, system)
        return {"session_id": session_id, "content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话记忆"""
    engine.memory.clear_session(session_id)
    return {"message": f"session {session_id} cleared"}


# ── 记忆管理 ──

@router.get("/session/{session_id}/context")
async def get_context(session_id: str, last_n: int | None = None):
    """获取会话上下文"""
    messages = engine.memory.get_context(session_id, last_n)
    return {"session_id": session_id, "messages": [m.model_dump() for m in messages]}


app.include_router(router)

# ── 流式输出 API ──
from src.api.streaming import router as streaming_router

app.include_router(streaming_router)

# ── 人工干预 API ──
from src.api.human_intervention import router as human_router

app.include_router(human_router)

# ── 数据查询 API ──
from src.api.data import router as data_router

app.include_router(data_router)
