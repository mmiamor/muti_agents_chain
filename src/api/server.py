"""
FastAPI HTTP 服务
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 AI Backend starting up...")
    yield
    logger.info("👋 AI Backend shutting down...")


app = FastAPI(
    title="LLMChain AI Backend",
    description="自动化 AI 后台服务",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
