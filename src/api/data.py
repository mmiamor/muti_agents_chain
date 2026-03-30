"""
数据查询API - 查询历史记录和统计数据
"""
from fastapi import APIRouter, HTTPException

from src.services.persistence_service import get_persistence_service

router = APIRouter(prefix="/api/v1/data", tags=["data"])


@router.get("/threads")
async def get_threads(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
):
    """获取所有会话线程列表"""
    service = get_persistence_service()
    threads = await service.get_all_threads(limit=limit, offset=offset, status=status)
    return {
        "count": len(threads),
        "threads": threads
    }


@router.get("/threads/{thread_id}")
async def get_thread_detail(thread_id: str):
    """获取会话线程详情，包含所有产出物和消息"""
    service = get_persistence_service()
    thread_data = await service.load_thread(thread_id)

    if not thread_data:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    return thread_data


@router.get("/artifacts")
async def search_artifacts(
    artifact_type: str | None = None,
    agent_name: str | None = None,
    limit: int = 20,
):
    """搜索产出物"""
    service = get_persistence_service()
    artifacts = await service.search_artifacts(
        artifact_type=artifact_type,
        agent_name=agent_name,
        limit=limit
    )
    return {
        "count": len(artifacts),
        "artifacts": artifacts
    }


@router.get("/threads/{thread_id}/metrics")
async def get_thread_metrics(thread_id: str):
    """获取线程的性能指标"""
    service = get_persistence_service()
    metrics = await service.get_thread_metrics(thread_id)

    if not metrics or metrics.get("total_calls", 0) == 0:
        raise HTTPException(status_code=404, detail=f"No metrics found for thread {thread_id}")

    return metrics