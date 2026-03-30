"""
数据库模型 - 持久化存储Agent产出物和会话历史
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text, create_engine)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship, select)
from sqlalchemy.pool import NullPool

from src.models.document_models import (PRD, TRD, DesignDocument,
                                        BackendCodeSpec, FrontendCodeSpec, QAReport)


class Base(DeclarativeBase):
    pass


class Thread(Base):
    """会话线程表"""
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.now)
    status: Mapped[str] = mapped_column(String, default="running")  # running, completed, failed, intervention
    current_phase: Mapped[str] = mapped_column(String, nullable=True)
    user_message: Mapped[str] = mapped_column(Text)
    total_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 关联的产出物
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="thread", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="thread", cascade="all, delete-orphan"
    )


class Artifact(Base):
    """产出物表"""
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id", ondelete="CASCADE"))
    artifact_type: Mapped[str] = mapped_column(String)  # prd, trd, design_doc, backend_code, frontend_code, qa_report
    agent_name: Mapped[str] = mapped_column(String)  # pm_agent, architect_agent, etc.
    version: Mapped[int] = mapped_column(Integer, default=1)  # 修订版本号
    content: Mapped[str] = mapped_column(Text)  # JSON格式的产出物内容
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关联
    thread: Mapped["Thread"] = relationship("Thread", back_populates="artifacts")


class Review(Base):
    """审查记录表"""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id", ondelete="CASCADE"))
    agent_name: Mapped[str] = mapped_column(String)  # 被审查的Agent
    status: Mapped[str] = mapped_column(String)  # APPROVED, REJECTED
    comments: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    revision_count: Mapped[int] = mapped_column(Integer, default=0)

    # 关联
    thread: Mapped["Thread"] = relationship("Thread", back_populates="reviews")


class Message(Base):
    """消息历史表"""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String)  # system, human, ai, tool
    content: Mapped[str] = mapped_column(Text)
    agent_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 关联
    thread: Mapped["Thread"] = relationship("Thread", backref="messages")


class HumanIntervention(Base):
    """人工干预任务表"""
    __tablename__ = "human_interventions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id", ondelete="CASCADE"))
    agent_name: Mapped[str] = mapped_column(String)
    artifact_type: Mapped[str] = mapped_column(String)
    review_comments: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, resolved, ignored
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关联
    thread: Mapped["Thread"] = relationship("Thread")


class PerformanceMetrics(Base):
    """性能指标表"""
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id", ondelete="CASCADE"))
    agent_name: Mapped[str] = mapped_column(String)
    execution_time: Mapped[float] = mapped_column(Float)  # 执行时间（秒）
    tokens_used: Mapped[int] = mapped_column(Integer)  # 使用的token数
    status: Mapped[str] = mapped_column(String)  # success, failed, timeout
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 关联
    thread: Mapped["Thread"] = relationship("Thread")


# 全局引擎
_engine = None
_async_engine = None


def get_engine(url: str | None = None):
    """获取同步数据库引擎"""
    global _engine
    if _engine is None:
        database_url = url or "sqlite+pysqlite:///./data/app.db"
        _engine = create_engine(database_url)
    return _engine


def get_async_engine(url: str | None = None):
    """获取异步数据库引擎"""
    global _async_engine
    if _async_engine is None:
        database_url = url or "sqlite+aiosqlite:///./data/app.db"
        _async_engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            poolclass=NullPool,  # SQLite不需要连接池
        )
    return _async_engine


async def init_database():
    """初始化数据库表"""
    engine = get_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialized successfully")


async def get_session() -> AsyncSession:
    """获取数据库会话"""
    engine = get_async_engine()
    async with AsyncSession(engine) as session:
        yield session
