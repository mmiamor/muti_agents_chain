"""
监控 API - 提供监控数据查询和告警管理接口
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from src.services.monitoring import (
    get_monitoring_manager,
    PerformanceMetric,
    ErrorRecord,
    ExecutionTrace,
    Alert,
    AlertRule,
)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

monitoring = get_monitoring_manager()


# ==================== Response 模型 ====================

class MetricsSummaryResponse(BaseModel):
    """指标摘要响应"""
    total_metrics: int
    total_errors: int
    active_traces: int
    total_alerts: int
    aggregates: dict


class MetricResponse(BaseModel):
    """指标响应"""
    id: str
    timestamp: datetime
    workflow_name: str
    execution_id: str
    stage_name: str
    agent_name: str
    metric_name: str
    value: float
    unit: str
    labels: dict


class ErrorResponse(BaseModel):
    """错误响应"""
    id: str
    timestamp: datetime
    workflow_name: str
    execution_id: str
    stage_name: Optional[str]
    agent_name: Optional[str]
    error_type: str
    error_message: str
    severity: str
    resolved: bool


class AlertResponse(BaseModel):
    """告警响应"""
    id: str
    timestamp: datetime
    rule_name: str
    severity: str
    message: str
    current_value: float
    threshold: float
    resolved: bool


class AlertRuleCreateRequest(BaseModel):
    """创建告警规则请求"""
    name: str
    metric_name: str
    condition: str  # gt, lt, eq, ne
    threshold: float
    severity: str = "warning"
    description: str = ""


class DashboardData(BaseModel):
    """仪表板数据"""
    summary: MetricsSummaryResponse
    recent_metrics: List[MetricResponse]
    recent_errors: List[ErrorResponse]
    active_alerts: List[AlertResponse]
    execution_stats: dict


# ==================== API 端点 ====================

@router.get("/summary", response_model=MetricsSummaryResponse)
async def get_monitoring_summary():
    """
    获取监控摘要

    Returns:
        监控摘要
    """
    try:
        summary = monitoring.get_metrics_summary()
        return MetricsSummaryResponse(**summary)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控摘要失败: {str(e)}"
        )


@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    workflow_name: Optional[str] = Query(None, description="工作流名称"),
    execution_id: Optional[str] = Query(None, description="执行 ID"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
):
    """
    获取性能指标

    Args:
        workflow_name: 工作流名称过滤
        execution_id: 执行 ID 过滤
        limit: 限制数量

    Returns:
        指标列表
    """
    try:
        metrics = monitoring.get_metrics(
            workflow_name=workflow_name,
            execution_id=execution_id,
            limit=limit,
        )

        return [MetricResponse(**m.model_dump()) for m in metrics]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取指标失败: {str(e)}"
        )


@router.get("/errors", response_model=List[ErrorResponse])
async def get_errors(
    workflow_name: Optional[str] = Query(None, description="工作流名称"),
    execution_id: Optional[str] = Query(None, description="执行 ID"),
    severity: Optional[str] = Query(None, description="严重程度"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
):
    """
    获取错误记录

    Args:
        workflow_name: 工作流名称过滤
        execution_id: 执行 ID 过滤
        severity: 严重程度过滤
        limit: 限制数量

    Returns:
        错误列表
    """
    try:
        errors = monitoring.get_errors(
            workflow_name=workflow_name,
            execution_id=execution_id,
            severity=severity,
            limit=limit,
        )

        return [ErrorResponse(**e.model_dump()) for e in errors]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取错误记录失败: {str(e)}"
        )


@router.get("/traces/{execution_id}", response_model=ExecutionTrace)
async def get_execution_trace(execution_id: str):
    """
    获取执行追踪

    Args:
        execution_id: 执行 ID

    Returns:
        执行追踪
    """
    try:
        trace = monitoring.get_trace(execution_id)

        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"执行追踪不存在: {execution_id}"
            )

        return trace

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行追踪失败: {str(e)}"
        )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = Query(None, description="严重程度"),
    resolved: Optional[bool] = Query(None, description="是否已解决"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
):
    """
    获取告警

    Args:
        severity: 严重程度过滤
        resolved: 是否已解决
        limit: 限制数量

    Returns:
        告警列表
    """
    try:
        alerts = monitoring.get_alerts(
            severity=severity,
            resolved=resolved,
            limit=limit,
        )

        return [AlertResponse(**a.model_dump()) for a in alerts]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取告警失败: {str(e)}"
        )


@router.post("/alerts/rules", response_model=AlertRule, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(request: AlertRuleCreateRequest):
    """
    创建告警规则

    Args:
        request: 告警规则创建请求

    Returns:
        创建的告警规则
    """
    try:
        rule = monitoring.add_alert_rule(
            name=request.name,
            metric_name=request.metric_name,
            condition=request.condition,
            threshold=request.threshold,
            severity=request.severity,
            description=request.description,
        )

        return rule

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建告警规则失败: {str(e)}"
        )


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    workflow_name: Optional[str] = Query(None, description="工作流名称"),
):
    """
    获取仪表板数据

    Args:
        workflow_name: 工作流名称过滤

    Returns:
        仪表板数据
    """
    try:
        # 获取摘要
        summary = monitoring.get_metrics_summary()

        # 获取最近的指标
        recent_metrics = monitoring.get_metrics(
            workflow_name=workflow_name,
            limit=50,
        )

        # 获取最近的错误
        recent_errors = monitoring.get_errors(
            workflow_name=workflow_name,
            limit=20,
        )

        # 获取活跃的告警
        active_alerts = monitoring.get_alerts(
            resolved=False,
            limit=50,
        )

        # 计算执行统计
        execution_stats = _calculate_execution_stats(workflow_name)

        return DashboardData(
            summary=MetricsSummaryResponse(**summary),
            recent_metrics=[MetricResponse(**m.model_dump()) for m in recent_metrics],
            recent_errors=[ErrorResponse(**e.model_dump()) for e in recent_errors],
            active_alerts=[AlertResponse(**a.model_dump()) for a in active_alerts],
            execution_stats=execution_stats,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仪表板数据失败: {str(e)}"
        )


def _calculate_execution_stats(workflow_name: Optional[str]) -> dict:
    """计算执行统计"""
    traces = list(monitoring.traces.values())

    if workflow_name:
        traces = [t for t in traces if t.workflow_name == workflow_name]

    total = len(traces)
    completed = len([t for t in traces if t.status == "completed"])
    failed = len([t for t in traces if t.status == "failed"])
    running = len([t for t in traces if t.status == "running"])

    # 计算平均执行时间
    completed_traces = [t for t in traces if t.status == "completed" and t.total_duration]
    avg_duration = (
        sum(t.total_duration for t in completed_traces) / len(completed_traces)
        if completed_traces else 0
    )

    return {
        "total_executions": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "success_rate": completed / total if total > 0 else 0,
        "avg_duration_seconds": avg_duration,
    }


__all__ = ["router"]
