"""
核心模块

注意：Engine/Scheduler/Pipeline 延迟导入，避免模块加载时就需要环境变量。
使用时直接 from src.core.engine import Engine。
"""
from .pipeline import Pipeline

__all__ = ["Pipeline"]
