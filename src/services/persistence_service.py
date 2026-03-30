"""
持久化服务 - 保存和查询Agent产出物
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (Artifact, HumanIntervention, Message,
                                     PerformanceMetrics, Review, Thread,
                                     get_session)
from src.models.document_models import (PRD, TRD, DesignDocument,
                                        BackendCodeSpec, FrontendCodeSpec, QAReport)
from src.models.agent_models import ReviewFeedback
from src.utils.logger import setup_logger

logger = setup_logger("persistence")


class PersistenceService:
    """持久化服务 - 保存和查询Agent产出物"""

    async def save_artifact(
        self,
        thread_id: str,
        agent_name: str,
        artifact_type: str,
        artifact: Any,
        is_approved: bool = False,
        version: int = 1,
    ) -> Artifact:
        """保存产出物到数据库"""
        async with get_session() as session:
            # 序列化产出物为JSON
            if hasattr(artifact, "model_dump"):
                content = artifact.model_dump_json()
            else:
                content = json.dumps(artifact)

            artifact_record = Artifact(
                thread_id=thread_id,
                artifact_type=artifact_type,
                agent_name=agent_name,
                version=version,
                content=content,
                is_approved=is_approved,
            )

            session.add(artifact_record)
            await session.commit()
            await session.refresh(artifact_record)

            logger.info(
                f"[Persistence] Saved artifact: {artifact_type} "
                f"from {agent_name} (v{version})"
            )

            return artifact_record

    async def save_review(
        self,
        thread_id: str,
        agent_name: str,
        review: ReviewFeedback,
        revision_count: int = 0,
    ) -> Review:
        """保存审查结果"""
        async with get_session() as session:
            review_record = Review(
                thread_id=thread_id,
                agent_name=agent_name,
                status=review.status,
                comments=review.comments,
                revision_count=revision_count,
            )

            session.add(review_record)
            await session.commit()
            await session.refresh(review_record)

            logger.info(
                f"[Persistence] Saved review: {review.status} "
                f"for {agent_name} (r{revision_count})"
            )

            return review_record

    async def save_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
    ) -> Message:
        """保存消息到历史"""
        async with get_session() as session:
            message_record = Message(
                thread_id=thread_id,
                role=role,
                content=content,
                agent_name=agent_name,
            )

            session.add(message_record)
            await session.commit()
            await session.refresh(message_record)

            return message_record

    async def save_metrics(
        self,
        thread_id: str,
        agent_name: str,
        execution_time: float,
        tokens_used: int,
        status: str,
        error_message: Optional[str] = None,
    ):
        """保存性能指标"""
        async with get_session() as session:
            metrics_record = PerformanceMetrics(
                thread_id=thread_id,
                agent_name=agent_name,
                execution_time=execution_time,
                tokens_used=tokens_used,
                status=status,
                error_message=error_message,
            )

            session.add(metrics_record)
            await session.commit()

            logger.debug(
                f"[Persistence] Saved metrics: {agent_name} "
                f"time={execution_time:.2f}s tokens={tokens_used}"
            )

    async def create_thread(
        self,
        thread_id: str,
        user_message: str,
        current_phase: str = "requirement_gathering",
    ) -> Thread:
        """创建新会话线程"""
        async with get_session() as session:
            thread = Thread(
                id=thread_id,
                user_message=user_message,
                current_phase=current_phase,
                status="running",
            )

            session.add(thread)
            await session.commit()
            await session.refresh(thread)

            logger.info(f"[Persistence] Created thread: {thread_id}")

            return thread

    async def update_thread_status(
        self,
        thread_id: str,
        status: str,
        current_phase: Optional[str] = None,
        total_duration: Optional[float] = None,
    ):
        """更新线程状态"""
        async with get_session() as session:
            thread = await session.get(Thread, thread_id)
            if thread:
                thread.status = status
                if current_phase:
                    thread.current_phase = current_phase
                if total_duration is not None:
                    thread.total_duration = total_duration

                await session.commit()
                logger.info(f"[Persistence] Updated thread {thread_id}: {status}")

    async def load_thread(self, thread_id: str) -> Optional[dict]:
        """加载完整会话历史"""
        async with get_session() as session:
            # 加载线程信息
            thread = await session.get(Thread, thread_id)
            if not thread:
                return None

            # 加载所有产出物
            artifacts_result = await session.execute(
                select(Artifact).where(Artifact.thread_id == thread_id)
            )
            artifacts = {}
            async for artifact in artifacts_result.scalars():
                artifacts[artifact.artifact_type] = {
                    "version": artifact.version,
                    "agent": artifact.agent_name,
                    "content": artifact.content,
                    "is_approved": artifact.is_approved,
                    "created_at": artifact.created_at.isoformat(),
                }

            # 加载所有审查记录
            reviews_result = await session.execute(
                select(Review).where(Review.thread_id == thread_id)
            )
            reviews = []
            async for review in reviews_result.scalars():
                reviews.append({
                    "agent_name": review.agent_name,
                    "status": review.status,
                    "comments": review.comments,
                    "revision_count": review.revision_count,
                    "created_at": review.created_at.isoformat(),
                })

            # 加载消息历史
            messages_result = await session.execute(
                select(Message).where(Message.thread_id == thread_id)
            )
            messages = []
            async for message in messages_result.scalars():
                messages.append({
                    "role": message.role,
                    "content": message.content,
                    "agent_name": message.agent_name,
                    "created_at": message.created_at.isoformat(),
                })

            return {
                "thread": {
                    "id": thread.id,
                    "status": thread.status,
                    "current_phase": thread.current_phase,
                    "user_message": thread.user_message,
                    "created_at": thread.created_at.isoformat(),
                    "updated_at": thread.updated_at.isoformat(),
                    "total_duration": thread.total_duration,
                },
                "artifacts": artifacts,
                "reviews": reviews,
                "messages": messages,
            }

    async def get_all_threads(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list[dict]:
        """获取所有会话线程列表"""
        async with get_session() as session:
            query = select(Thread).order_by(Thread.created_at.desc())

            if status:
                query = query.where(Thread.status == status)

            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            threads = []

            for thread in result.scalars():
                threads.append({
                    "id": thread.id,
                    "status": thread.status,
                    "current_phase": thread.current_phase,
                    "user_message": thread.user_message[:100] + "...",
                    "created_at": thread.created_at.isoformat(),
                    "updated_at": thread.updated_at.isoformat(),
                    "total_duration": thread.total_duration,
                })

            return threads

    async def search_artifacts(
        self,
        artifact_type: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """搜索产出物"""
        async with get_session() as session:
            query = select(Artifact).order_by(Artifact.created_at.desc())

            if artifact_type:
                query = query.where(Artifact.artifact_type == artifact_type)
            if agent_name:
                query = query.where(Artifact.agent_name == agent_name)

            query = query.limit(limit)

            result = await session.execute(query)
            artifacts = []

            for artifact in result.scalars():
                artifacts.append({
                    "id": artifact.id,
                    "thread_id": artifact.thread_id,
                    "artifact_type": artifact.artifact_type,
                    "agent_name": artifact.agent_name,
                    "version": artifact.version,
                    "is_approved": artifact.is_approved,
                    "created_at": artifact.created_at.isoformat(),
                })

            return artifacts

    async def get_thread_metrics(self, thread_id: str) -> dict:
        """获取线程的性能指标"""
        async with get_session() as session:
            result = await session.execute(
                select(PerformanceMetrics).where(
                    PerformanceMetrics.thread_id == thread_id
                )
            )

            metrics = []
            async for metric in result.scalars():
                metrics.append({
                    "agent_name": metric.agent_name,
                    "execution_time": metric.execution_time,
                    "tokens_used": metric.tokens_used,
                    "status": metric.status,
                    "error_message": metric.error_message,
                    "created_at": metric.created_at.isoformat(),
                })

            # 汇总统计
            total_calls = len(metrics)
            total_time = sum(m["execution_time"] for m in metrics)
            total_tokens = sum(m["tokens_used"] for m in metrics)
            successful_calls = sum(1 for m in metrics if m["status"] == "success")

            return {
                "thread_id": thread_id,
                "total_calls": total_calls,
                "total_time": total_time,
                "total_tokens": total_tokens,
                "successful_calls": successful_calls,
                "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
                "metrics": metrics,
            }


# 人工干预服务
class HumanInterventionService:
    """人工干预服务 - 管理需要人工处理的任务"""

    async def create_intervention_task(
        self,
        thread_id: str,
        agent_name: str,
        artifact_type: str,
        review_comments: str,
        artifact_content: Any,
    ) -> HumanIntervention:
        """创建人工干预任务"""
        async with get_session() as session:
            # 序列化artifact内容
            if hasattr(artifact_content, "model_dump_json"):
                content = artifact_content.model_dump_json()
            else:
                content = json.dumps(artifact_content)

            intervention = HumanIntervention(
                thread_id=thread_id,
                agent_name=agent_name,
                artifact_type=artifact_type,
                review_comments=review_comments,
                status="pending",
            )

            session.add(intervention)
            await session.commit()
            await session.refresh(intervention)

            logger.warning(
                f"[HumanIntervention] Created task for {agent_name}: "
                f"task_id={intervention.id}"
            )

            return intervention

    async def get_pending_tasks(self) -> list[dict]:
        """获取所有待处理的任务"""
        async with get_session() as session:
            result = await session.execute(
                select(HumanIntervention)
                .where(HumanIntervention.status == "pending")
                .order_by(HumanIntervention.created_at.asc())
            )

            tasks = []
            async for task in result.scalars():
                # 加载关联的thread信息
                thread = await session.get(Thread, task.thread_id)

                tasks.append({
                    "id": task.id,
                    "thread_id": task.thread_id,
                    "agent_name": task.agent_name,
                    "artifact_type": task.artifact_type,
                    "review_comments": task.review_comments,
                    "created_at": task.created_at.isoformat(),
                    "user_message": thread.user_message if thread else "",
                })

            return tasks

    async def resolve_intervention(
        self,
        task_id: str,
        resolution_type: str,  # approved, rejected, ignored
        feedback: str,
    ) -> HumanIntervention:
        """解决人工干预任务"""
        async with get_session() as session:
            intervention = await session.get(HumanIntervention, task_id)
            if not intervention:
                raise ValueError(f"Task {task_id} not found")

            intervention.status = "resolved"
            intervention.resolution = f"{resolution_type}: {feedback}"
            intervention.resolved_at = datetime.now()

            await session.commit()
            await session.refresh(intervention)

            logger.info(f"[HumanIntervention] Resolved task {task_id}: {resolution_type}")

            return intervention

    async def get_intervention(self, task_id: str) -> Optional[dict]:
        """获取干预任务详情"""
        async with get_session() as session:
            intervention = await session.get(HumanIntervention, task_id)
            if not intervention:
                return None

            # 加载artifact内容
            artifacts_result = await session.execute(
                select(Artifact).where(
                    Artifact.thread_id == intervention.thread_id,
                    Artifact.artifact_type == intervention.artifact_type
                ).order_by(Artifact.version.desc())
            )

            latest_artifact = None
            async for artifact in artifacts_result.scalars():
                latest_artifact = {
                    "version": artifact.version,
                    "content": artifact.content,
                    "created_at": artifact.created_at.isoformat(),
                }
                break

            return {
                "id": intervention.id,
                "thread_id": intervention.thread_id,
                "agent_name": intervention.agent_name,
                "artifact_type": intervention.artifact_type,
                "review_comments": intervention.review_comments,
                "status": intervention.status,
                "resolution": intervention.resolution,
                "created_at": intervention.created_at.isoformat(),
                "resolved_at": intervention.resolved_at.isoformat() if intervention.resolved_at else None,
                "latest_artifact": latest_artifact,
            }


# 全局服务实例
_persistence_service: Optional[PersistenceService] = None
_human_intervention_service: Optional[HumanInterventionService] = None


def get_persistence_service() -> PersistenceService:
    """获取持久化服务实例"""
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = PersistenceService()
    return _persistence_service


def get_human_intervention_service() -> HumanInterventionService:
    """获取人工干预服务实例"""
    global _human_intervention_service
    if _human_intervention_service is None:
        _human_intervention_service = HumanInterventionService()
    return _human_intervention_service
