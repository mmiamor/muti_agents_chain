"""
监控系统 - 工作流执行追踪、性能指标收集、错误报告
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.utils.logger import setup_logger

logger = setup_logger("monitoring")


# ==================== 数据模型 ====================

class MetricType(str):
    """指标类型"""
    COUNTER = "counter"      # 计数器
    GAUGE = "gauge"          # 仪表
    HISTOGRAM = "histogram"  # 直方图


class PerformanceMetric(BaseModel):
    """性能指标"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    workflow_name: str
    execution_id: str
    stage_name: str
    agent_name: str
    metric_type: str
    metric_name: str
    value: float
    unit: str = "ms"  # ms, seconds, count, bytes
    labels: Dict[str, str] = Field(default_factory=dict)


class ErrorRecord(BaseModel):
    """错误记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    workflow_name: str
    execution_id: str
    stage_name: Optional[str] = None
    agent_name: Optional[str] = None
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    severity: str = "error"  # error, warning, critical
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class ExecutionTrace(BaseModel):
    """执行追踪"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    workflow_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled
    total_duration: Optional[float] = None
    stages_completed: int = 0
    total_stages: int
    input_summary: str = ""
    output_summary: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertRule(BaseModel):
    """告警规则"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    metric_name: str
    condition: str  # gt, lt, eq, ne
    threshold: float
    severity: str = "warning"  # info, warning, critical
    enabled: bool = True
    notification_channels: List[str] = Field(default_factory=list)


class Alert(BaseModel):
    """告警"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    rule_id: str
    rule_name: str
    severity: str
    message: str
    current_value: float
    threshold: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None


# ==================== 监控管理器 ====================

class MonitoringManager:
    """监控管理器 - 单例模式"""

    _instance: Optional["MonitoringManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # 存储
        self.metrics: List[PerformanceMetric] = []
        self.errors: List[ErrorRecord] = []
        self.traces: Dict[str, ExecutionTrace] = {}
        self.alerts: List[Alert] = []
        self.alert_rules: List[AlertRule] = []

        # 指标聚合
        self.metric_aggregates: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "count": 0,
            "sum": 0,
            "avg": 0,
            "min": float("inf"),
            "max": float("-inf"),
        })

        # 启动清理任务
        self._start_cleanup_task()

    def record_metric(
        self,
        workflow_name: str,
        execution_id: str,
        stage_name: str,
        agent_name: str,
        metric_name: str,
        value: float,
        metric_type: str = "gauge",
        unit: str = "ms",
        labels: Optional[Dict[str, str]] = None,
    ):
        """
        记录性能指标

        Args:
            workflow_name: 工作流名称
            execution_id: 执行 ID
            stage_name: 阶段名称
            agent_name: Agent 名称
            metric_name: 指标名称
            value: 指标值
            metric_type: 指标类型
            unit: 单位
            labels: 标签
        """
        metric = PerformanceMetric(
            workflow_name=workflow_name,
            execution_id=execution_id,
            stage_name=stage_name,
            agent_name=agent_name,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            labels=labels or {},
        )

        self.metrics.append(metric)

        # 更新聚合
        key = f"{workflow_name}.{agent_name}.{metric_name}"
        agg = self.metric_aggregates[key]
        agg["count"] += 1
        agg["sum"] += value
        agg["avg"] = agg["sum"] / agg["count"]
        agg["min"] = min(agg["min"], value)
        agg["max"] = max(agg["max"], value)

        # 检查告警
        self._check_alerts(metric)

        logger.debug(f"记录指标: {metric_name}={value}{unit}")

    def record_error(
        self,
        workflow_name: str,
        execution_id: str,
        error_type: str,
        error_message: str,
        stage_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        stack_trace: Optional[str] = None,
        severity: str = "error",
    ):
        """
        记录错误

        Args:
            workflow_name: 工作流名称
            execution_id: 执行 ID
            error_type: 错误类型
            error_message: 错误消息
            stage_name: 阶段名称
            agent_name: Agent 名称
            stack_trace: 堆栈跟踪
            severity: 严重程度
        """
        error = ErrorRecord(
            workflow_name=workflow_name,
            execution_id=execution_id,
            stage_name=stage_name,
            agent_name=agent_name,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            severity=severity,
        )

        self.errors.append(error)

        # 严重错误立即告警
        if severity in ["critical"]:
            self._create_alert(
                name=f"Critical Error: {error_type}",
                severity="critical",
                message=f"Critical error in {workflow_name}: {error_message}",
                metric_name="error",
                current_value=1,
                threshold=0,
            )

        logger.error(f"记录错误: {error_type} - {error_message}")

    def start_trace(
        self,
        execution_id: str,
        workflow_name: str,
        total_stages: int,
        input_summary: str = "",
    ) -> ExecutionTrace:
        """
        开始执行追踪

        Args:
            execution_id: 执行 ID
            workflow_name: 工作流名称
            total_stages: 总阶段数
            input_summary: 输入摘要

        Returns:
            执行追踪对象
        """
        trace = ExecutionTrace(
            execution_id=execution_id,
            workflow_name=workflow_name,
            started_at=datetime.now(),
            total_stages=total_stages,
            input_summary=input_summary,
        )

        self.traces[execution_id] = trace
        return trace

    def update_trace(
        self,
        execution_id: str,
        stages_completed: int,
        status: Optional[str] = None,
        output_summary: Optional[str] = None,
    ):
        """
        更新执行追踪

        Args:
            execution_id: 执行 ID
            stages_completed: 已完成阶段数
            status: 状态
            output_summary: 输出摘要
        """
        if execution_id not in self.traces:
            return

        trace = self.traces[execution_id]
        trace.stages_completed = stages_completed

        if status:
            trace.status = status

        if output_summary:
            trace.output_summary = output_summary

        if status in ["completed", "failed", "cancelled"]:
            trace.completed_at = datetime.now()
            trace.total_duration = (trace.completed_at - trace.started_at).total_seconds()

    def add_alert_rule(
        self,
        name: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: str = "warning",
        description: str = "",
    ) -> AlertRule:
        """
        添加告警规则

        Args:
            name: 规则名称
            metric_name: 指标名称
            condition: 条件 (gt, lt, eq, ne)
            threshold: 阈值
            severity: 严重程度
            description: 描述

        Returns:
            告警规则
        """
        rule = AlertRule(
            name=name,
            description=description,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            severity=severity,
        )

        self.alert_rules.append(rule)
        logger.info(f"添加告警规则: {name}")
        return rule

    def _check_alerts(self, metric: PerformanceMetric):
        """检查告警"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            if rule.metric_name != metric.metric_name:
                continue

            triggered = False
            if rule.condition == "gt" and metric.value > rule.threshold:
                triggered = True
            elif rule.condition == "lt" and metric.value < rule.threshold:
                triggered = True
            elif rule.condition == "eq" and metric.value == rule.threshold:
                triggered = True
            elif rule.condition == "ne" and metric.value != rule.threshold:
                triggered = True

            if triggered:
                self._create_alert(
                    name=rule.name,
                    severity=rule.severity,
                    message=f"告警: {metric.metric_name}={metric.value}{metric.unit} (阈值: {rule.threshold})",
                    metric_name=metric.metric_name,
                    current_value=metric.value,
                    threshold=rule.threshold,
                )

    def _create_alert(
        self,
        name: str,
        severity: str,
        message: str,
        metric_name: str,
        current_value: float,
        threshold: float,
    ):
        """创建告警"""
        alert = Alert(
            rule_name=name,
            severity=severity,
            message=message,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
        )

        self.alerts.append(alert)
        logger.warning(f"告警触发: {message}")

    def get_metrics(
        self,
        workflow_name: Optional[str] = None,
        execution_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[PerformanceMetric]:
        """
        获取指标

        Args:
            workflow_name: 工作流名称过滤
            execution_id: 执行 ID 过滤
            limit: 限制数量

        Returns:
            指标列表
        """
        metrics = self.metrics

        if workflow_name:
            metrics = [m for m in metrics if m.workflow_name == workflow_name]

        if execution_id:
            metrics = [m for m in metrics if m.execution_id == execution_id]

        return metrics[-limit:]

    def get_errors(
        self,
        workflow_name: Optional[str] = None,
        execution_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[ErrorRecord]:
        """
        获取错误

        Args:
            workflow_name: 工作流名称过滤
            execution_id: 执行 ID 过滤
            severity: 严重程度过滤
            limit: 限制数量

        Returns:
            错误列表
        """
        errors = self.errors

        if workflow_name:
            errors = [e for e in errors if e.workflow_name == workflow_name]

        if execution_id:
            errors = [e for e in errors if e.execution_id == execution_id]

        if severity:
            errors = [e for e in errors if e.severity == severity]

        return errors[-limit:]

    def get_trace(self, execution_id: str) -> Optional[ExecutionTrace]:
        """获取执行追踪"""
        return self.traces.get(execution_id)

    def get_alerts(
        self,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """
        获取告警

        Args:
            severity: 严重程度过滤
            resolved: 是否已解决
            limit: 限制数量

        Returns:
            告警列表
        """
        alerts = self.alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        return alerts[-limit:]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            "total_metrics": len(self.metrics),
            "total_errors": len(self.errors),
            "active_traces": len(self.traces),
            "total_alerts": len(self.alerts),
            "aggregates": dict(self.metric_aggregates),
        }

    def _start_cleanup_task(self):
        """启动清理任务"""
        # 清理 7 天前的数据
        cutoff = datetime.now() - timedelta(days=7)

        self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
        self.errors = [e for e in self.errors if e.timestamp > cutoff]
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff]

        # 清理已完成的追踪
        self.traces = {
            k: v for k, v in self.traces.items()
            if v.status == "running" or (v.completed_at and v.completed_at > cutoff)
        }

        logger.info("监控数据清理完成")


# ==================== 装饰器 ====================

def monitor_execution(workflow_name: str, execution_id: str):
    """
    监控执行装饰器

    Args:
        workflow_name: 工作流名称
        execution_id: 执行 ID
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitoring = MonitoringManager()

            stage_name = kwargs.get("stage_name", "unknown")
            agent_name = kwargs.get("agent_name", "unknown")

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # 记录执行时间
                duration = (time.time() - start_time) * 1000  # ms
                monitoring.record_metric(
                    workflow_name=workflow_name,
                    execution_id=execution_id,
                    stage_name=stage_name,
                    agent_name=agent_name,
                    metric_name="execution_time",
                    value=duration,
                    unit="ms",
                )

                return result

            except Exception as e:
                # 记录错误
                monitoring.record_error(
                    workflow_name=workflow_name,
                    execution_id=execution_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stage_name=stage_name,
                    agent_name=agent_name,
                )
                raise

        return wrapper
    return decorator


# ==================== 便捷函数 ====================

def get_monitoring_manager() -> MonitoringManager:
    """获取监控管理器实例"""
    return MonitoringManager()


__all__ = [
    "MonitoringManager",
    "get_monitoring_manager",
    "monitor_execution",
    "PerformanceMetric",
    "ErrorRecord",
    "ExecutionTrace",
    "AlertRule",
    "Alert",
]
