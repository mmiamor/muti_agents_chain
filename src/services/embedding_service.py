"""
嵌入模型服务 - 提供 RAG 所需的嵌入能力

支持多种嵌入模型提供商：
- OpenAI Compatible APIs (包括智谱 AI)
- 本地嵌入模型（可选）
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from src.config import settings

logger = logging.getLogger("embedding_service")


def create_embeddings() -> Optional[Embeddings]:
    """
    创建嵌入模型实例

    使用配置的 OpenAI 兼容 API（如智谱 AI）

    Returns:
        Embeddings: 嵌入模型实例，如果配置不完整则返回 None
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, embeddings disabled")
        return None

    try:
        # 使用智谱 AI 的嵌入模型
        embeddings = OpenAIEmbeddings(
            model="embedding-2",  # 智谱 AI 的嵌入模型
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
        )

        logger.info(f"Created embeddings with base URL: {settings.OPENAI_BASE_URL}")
        return embeddings

    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}")
        return None


def create_in_memory_vector_store():
    """

    创建内存向量存储

    适用于开发和测试，生产环境建议使用持久化存储

    Returns:
        InMemoryVectorStore: 内存向量存储实例
    """
    try:
        from langchain_core.vectorstores import InMemoryVectorStore
        from langchain_core.embeddings import Embeddings

        embeddings = create_embeddings()
        if not embeddings:
            logger.warning("Cannot create vector store without embeddings")
            return None

        vector_store = InMemoryVectorStore(embeddings)
        logger.info("Created in-memory vector store")
        return vector_store

    except Exception as e:
        logger.error(f"Failed to create in-memory vector store: {e}")
        return None


def create_chroma_vector_store(collection_name: str = "prd_knowledge"):
    """
    创建 Chroma 持久化向量存储

    Args:
        collection_name: 集合名称

    Returns:
        Chroma: Chroma 向量存储实例
    """
    try:
        from langchain_chroma import Chroma
        import chromadb

        embeddings = create_embeddings()
        if not embeddings:
            logger.warning("Cannot create Chroma store without embeddings")
            return None

        # 创建持久化客户端
        client = chromadb.PersistentClient(path="./data/chroma_db")

        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            client=client,
        )

        logger.info(f"Created Chroma vector store with collection: {collection_name}")
        return vector_store

    except ImportError:
        logger.warning("langchain_chroma not installed, falling back to in-memory store")
        return create_in_memory_vector_store()
    except Exception as e:
        logger.error(f"Failed to create Chroma vector store: {e}")
        return create_in_memory_vector_store()


__all__ = [
    "create_embeddings",
    "create_in_memory_vector_store",
    "create_chroma_vector_store",
]
