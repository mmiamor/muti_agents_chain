"""
流式输出 API — 支持 Server-Sent Events (SSE)
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.config import settings
from src.core.orchestrator import build_graph
from src.models.state import AgentPhase

router = APIRouter(prefix="/api/v1/stream", tags=["streaming"])


class StreamEvent:
    """流式事件格式"""

    @staticmethod
    def phase(agent_name: str, phase: str, status: str = "running") -> str:
        """阶段事件"""
        return json.dumps({
            "type": "phase",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "agent": agent_name,
                "phase": phase,
                "status": status
            }
        }, ensure_ascii=False)

    @staticmethod
    def progress(agent_name: str, step: str, percent: int = 0, message: str = "") -> str:
        """进度事件"""
        return json.dumps({
            "type": "progress",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "agent": agent_name,
                "step": step,
                "percent": percent,
                "message": message
            }
        }, ensure_ascii=False)

    @staticmethod
    def artifact(agent_name: str, artifact_type: str, data: dict) -> str:
        """产出物事件"""
        return json.dumps({
            "type": "artifact",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "agent": agent_name,
                "artifact_type": artifact_type,
                "content": data
            }
        }, ensure_ascii=False)

    @staticmethod
    def thinking(agent_name: str, content: str) -> str:
        """思考过程事件"""
        return json.dumps({
            "type": "thinking",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "agent": agent_name,
                "content": content
            }
        }, ensure_ascii=False)

    @staticmethod
    def review(status: str, comments: str) -> str:
        """审查事件"""
        return json.dumps({
            "type": "review",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "status": status,
                "comments": comments
            }
        }, ensure_ascii=False)

    @staticmethod
    def error(error_type: str, message: str, details: str = "") -> str:
        """错误事件"""
        return json.dumps({
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "error_type": error_type,
                "message": message,
                "details": details
            }
        }, ensure_ascii=False)

    @staticmethod
    def done(final_result: dict) -> str:
        """完成事件"""
        return json.dumps({
            "type": "done",
            "timestamp": datetime.now().isoformat(),
            "data": final_result
        }, ensure_ascii=False)


async def stream_run_pipeline(
    message: str,
    thread_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    流式执行完整 Pipeline

    Args:
        message: 用户消息
        thread_id: 会话线程ID

    Yields:
        SSE 格式的流式事件
    """
    if not thread_id:
        thread_id = str(uuid.uuid4())

    start_time = datetime.now()

    try:
        # 发送开始事件
        yield StreamEvent.phase("system", "init", "starting")

        # 构建图
        graph = build_graph()
        config = {"configurable": {"thread_id": thread_id}}

        # 准备初始状态
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "current_phase": AgentPhase.REQUIREMENT_GATHERING,
            "sender": "user",
        }

        yield StreamEvent.progress("system", "graph_built", 10, "LangGraph 已构建")

        # 异步执行流程
        result = await graph.ainvoke(initial_state, config)

        # 处理结果并发送事件
        sender = result.get("sender", "unknown")
        revision_counts = result.get("revision_counts", {})

        # PRD 事件
        if result.get("prd"):
            prd = result["prd"]
            yield StreamEvent.artifact(
                "pm_agent",
                "prd",
                {
                    "vision": prd.vision,
                    "target_audience": prd.target_audience,
                    "core_features": prd.core_features,
                    "user_stories_count": len(prd.user_stories),
                }
            )

        # TRD 事件
        if result.get("trd"):
            trd = result["trd"]
            yield StreamEvent.artifact(
                "architect_agent",
                "trd",
                {
                    "tech_stack": {
                        "frontend": trd.tech_stack.frontend,
                        "backend": trd.tech_stack.backend,
                        "database": trd.tech_stack.database,
                    },
                    "api_count": len(trd.api_endpoints),
                }
            )

        # Design 事件
        if result.get("design_doc"):
            design = result["design_doc"]
            yield StreamEvent.artifact(
                "design_agent",
                "design_doc",
                {
                    "pages_count": len(design.page_specs),
                    "component_library": design.component_library,
                    "design_tokens": {
                        "primary": design.design_tokens.color_primary,
                    },
                }
            )

        # 审查结果事件
        if result.get("latest_review"):
            review = result["latest_review"]
            yield StreamEvent.review(review.status, review.comments)

        # 最终完成事件
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        final_result = {
            "thread_id": thread_id,
            "duration": duration,
            "sender": sender,
            "revision_counts": revision_counts,
            "has_prd": result.get("prd") is not None,
            "has_trd": result.get("trd") is not None,
            "has_design": result.get("design_doc") is not None,
            "final_status": "completed" if result.get("latest_review") else "incomplete",
        }

        yield StreamEvent.done(final_result)

    except Exception as e:
        # 错误事件
        yield StreamEvent.error(
            type(e).__name__,
            str(e),
            f"执行失败: {thread_id}"
        )


async def stream_run_agent(
    message: str,
    agent_name: str,
    thread_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    流式执行单个 Agent

    Args:
        message: 用户消息
        agent_name: 目标 Agent 名称
        thread_id: 会话线程ID

    Yields:
        SSE 格式的流式事件
    """
    if not thread_id:
        thread_id = str(uuid.uuid4())

    try:
        # 发送开始事件
        yield StreamEvent.phase(agent_name, "start", "running")
        yield StreamEvent.thinking(agent_name, f"开始处理用户需求...")

        # 构建图
        graph = build_graph()
        config = {"configurable": {"thread_id": thread_id}}

        # 根据不同的 agent 设置不同的初始阶段
        phase_mapping = {
            "pm_agent": AgentPhase.REQUIREMENT_GATHERING,
            "architect_agent": AgentPhase.ARCHITECTURE_DESIGN,
            "design_agent": AgentPhase.UI_DESIGN,
            "backend_dev_agent": AgentPhase.CODING,
            "frontend_dev_agent": AgentPhase.CODING,
            "qa_agent": AgentPhase.TESTING,
        }

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "current_phase": phase_mapping.get(agent_name, AgentPhase.REQUIREMENT_GATHERING),
            "sender": "user",
        }

        yield StreamEvent.progress(agent_name, "executing", 50, "正在调用 LLM...")

        # 执行
        result = await graph.ainvoke(initial_state, config)

        yield StreamEvent.progress(agent_name, "completed", 100, "执行完成")

        # 发送结果事件
        if agent_name == "pm_agent" and result.get("prd"):
            prd = result["prd"]
            yield StreamEvent.artifact(
                agent_name,
                "prd",
                {
                    "vision": prd.vision,
                    "target_audience": prd.target_audience,
                    "core_features": prd.core_features,
                }
            )

        elif agent_name == "architect_agent" and result.get("trd"):
            trd = result["trd"]
            yield StreamEvent.artifact(
                agent_name,
                "trd",
                {
                    "tech_stack": trd.tech_stack.model_dump(),
                    "architecture_overview": trd.architecture_overview[:200] + "...",
                }
            )

        # 最终完成
        yield StreamEvent.done({
            "thread_id": thread_id,
            "agent": agent_name,
            "status": "completed"
        })

    except Exception as e:
        yield StreamEvent.error(
            type(e).__name__,
            str(e),
            f"Agent {agent_name} 执行失败"
        )


# ── 路由定义 ──

@router.post("/run")
async def stream_run_full_pipeline(
    message: str,
    thread_id: str | None = None,
):
    """
    流式执行完整 Pipeline (PM → Architect → Design → ...)

    返回 Server-Sent Events (SSE) 格式的流式响应。

    事件类型:
    - phase: 阶段变更
    - progress: 进度更新
    - artifact: 产出物生成
    - thinking: 思考过程
    - review: 审查结果
    - error: 错误信息
    - done: 完成通知
    """
    return StreamingResponse(
        stream_run_pipeline(message, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@router.post("/agent/{agent_name}")
async def stream_run_single_agent(
    agent_name: str,
    message: str,
    thread_id: str | None = None,
):
    """
    流式执行单个 Agent

    支持的 Agent:
    - pm_agent: 产品经理
    - architect_agent: 架构师
    - design_agent: 设计师
    - backend_dev_agent: 后端开发
    - frontend_dev_agent: 前端开发
    - qa_agent: 质量保障
    """
    # 验证 agent 名称
    valid_agents = [
        "pm_agent",
        "architect_agent",
        "design_agent",
        "backend_dev_agent",
        "frontend_dev_agent",
        "qa_agent",
    ]

    if agent_name not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent name. Must be one of: {', '.join(valid_agents)}"
        )

    return StreamingResponse(
        stream_run_agent(message, agent_name, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
