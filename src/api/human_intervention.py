"""
人工干预API - 管理需要人工处理的任务
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.persistence_service import get_human_intervention_service

router = APIRouter(prefix="/api/v1/human", tags=["human-intervention"])


class InterventionResolution(BaseModel):
    """人工干预解决方案"""
    resolution_type: str = Field(..., description="approved, rejected, or ignored")
    feedback: str = Field(..., description="反馈意见或修改指导")


@router.get("/tasks/pending")
async def get_pending_tasks():
    """获取所有待处理的人工干预任务"""
    service = get_human_intervention_service()
    tasks = await service.get_pending_tasks()
    return {
        "count": len(tasks),
        "tasks": tasks
    }


@router.get("/tasks/{task_id}")
async def get_intervention_detail(task_id: str):
    """获取干预任务详情"""
    service = get_human_intervention_service()
    task = await service.get_intervention(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return task


@router.post("/tasks/{task_id}/resolve")
async def resolve_intervention(task_id: str, resolution: InterventionResolution):
    """解决人工干预任务"""
    service = get_human_intervention_service()

    try:
        resolved_task = await service.resolve_intervention(
            task_id,
            resolution.resolution_type,
            resolution.feedback
        )
        return {
            "message": f"Task {task_id} resolved",
            "task": resolved_task
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve task: {str(e)}")