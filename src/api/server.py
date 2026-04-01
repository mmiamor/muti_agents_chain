"""
FastAPI HTTP 服务 - 增强安全性和中间件
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("server")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    简单的速率限制中间件

    基于内存的请求计数，适合单机部署
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable):
        """处理请求速率限制"""
        # 获取客户端标识（IP 地址或 API Key）
        client_id = request.client.host if request.client else "unknown"

        current_time = time.time()

        # 清理过期记录
        if client_id in self.requests:
            self.requests[client_id] = [
                t for t in self.requests[client_id]
                if current_time - t < self.window_seconds
            ]
        else:
            self.requests[client_id] = []

        # 检查速率限制
        if len(self.requests[client_id]) >= self.max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        # 记录请求
        self.requests[client_id].append(current_time)

        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头中间件

    添加常见的安全响应头
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """添加安全头"""
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    记录请求的详细信息
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """记录请求和响应信息"""
        start_time = time.time()

        # 记录请求
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else "unknown",
            }
        )

        response = await call_next(request)

        # 记录响应
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} ({process_time:.3f}s)",
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )

        # 添加处理时间头
        response.headers["X-Process-Time"] = str(process_time)

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Omni Agent Graph starting up...")

    # 初始化资源
    # TODO: 初始化数据库连接、Redis 等

    yield

    logger.info("👋 Omni Agent Graph shutting down...")

    # 清理资源
    # TODO: 关闭数据库连接、Redis 等


# 创建 FastAPI 应用
app = FastAPI(
    title="Omni Agent Graph",
    description="全能型智能体编排系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
)

# 添加中间件（顺序很重要）
# 1. 安全头中间件（最先执行）
app.add_middleware(SecurityHeadersMiddleware)

# 2. 信任的主机中间件（生产环境应该配置）
if not settings.DEBUG:
    # 生产环境限制允许的主机
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # TODO: 配置实际允许的主机列表
    )

# 3. CORS 中间件
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )

# 4. GZip 压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 5. 速率限制中间件（仅在开发环境禁用，生产环境启用）
if not settings.DEBUG:
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=100,  # 每分钟最多 100 个请求
        window_seconds=60,
    )

# 6. 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)


# 异常处理器
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """处理值错误"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"} if not settings.DEBUG else {
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.ENABLE_API_DOCS else None,
    }
