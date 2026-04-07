"""
RAG 服务 - 从现有 PRD 库中检索相关知识

基于 LangChain 的向量存储和检索实现，支持：
- 从数据库中加载已存储的 PRD
- 将 PRD 转换为可检索的向量
- 语义相似度检索
- 上下文增强
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from src.config import settings
from src.database.models import Artifact, get_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger("rag_service")


class PRDKnowledgeBase:
    """PRD 知识库 - RAG 检索核心类"""

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        """
        初始化 PRD 知识库

        Args:
            embeddings: 嵌入模型实例
            vector_store: 向量存储实例（如 Chroma, FAISS 等）
        """
        self.embeddings = embeddings
        self.vector_store = vector_store
        self._initialized = False

    async def initialize(self):
        """初始化知识库，从数据库加载 PRD"""
        if self._initialized:
            return

        logger.info("Initializing PRD knowledge base from database...")

        # 从数据库加载所有已批准的 PRD
        prds = await self._load_approved_prds()

        if not prds:
            logger.warning("No approved PRDs found in database")
            self._initialized = True
            return

        # 转换为文档并索引
        documents = self._convert_prds_to_documents(prds)

        if self.vector_store and self.embeddings:
            await self._index_documents(documents)
            logger.info(f"Successfully indexed {len(documents)} PRD documents")
        else:
            logger.warning("Vector store or embeddings not configured, using in-memory search")

        self._initialized = True

    async def _load_approved_prds(self) -> list[dict]:
        """从数据库加载已批准的 PRD"""
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        prds = []
        try:
            async with async_session() as session:
                # 查询所有已批准的 PRD
                result = await session.execute(
                    select(Artifact)
                    .where(Artifact.artifact_type == "prd")
                    .where(Artifact.is_approved == True)
                    .order_by(Artifact.created_at.desc())
                )

                artifacts = result.scalars().all()

                for artifact in artifacts:
                    try:
                        prd_data = json.loads(artifact.content)
                        prd_data["metadata"] = {
                            "artifact_id": artifact.id,
                            "thread_id": artifact.thread_id,
                            "agent_name": artifact.agent_name,
                            "version": artifact.version,
                            "created_at": artifact.created_at.isoformat(),
                        }
                        prds.append(prd_data)
                    except Exception as e:
                        logger.error(f"Failed to parse PRD artifact {artifact.id}: {e}")

                logger.info(f"Loaded {len(prds)} approved PRDs from database")

        except Exception as e:
            logger.error(f"Failed to load PRDs from database: {e}")
        finally:
            await engine.dispose()

        return prds

    def _convert_prds_to_documents(self, prds: list[dict]) -> list[Document]:
        """将 PRD 数据转换为 LangChain 文档"""
        documents = []

        for prd in prds:
            metadata = prd.get("metadata", {})

            # 创建多个文档片段以提高检索精度
            # 1. 愿景和目标用户
            doc_vision = Document(
                page_content=f"""
产品愿景: {prd.get('vision', '')}
目标用户: {', '.join(prd.get('target_audience', []))}
非功能性需求: {prd.get('non_functional', '')}
                """.strip(),
                metadata={
                    **metadata,
                    "section": "vision",
                    "prd_id": metadata.get("artifact_id"),
                },
            )
            documents.append(doc_vision)

            # 2. 核心功能
            features = prd.get('core_features', [])
            if features:
                doc_features = Document(
                    page_content=f"核心功能: {', '.join(features)}",
                    metadata={
                        **metadata,
                        "section": "features",
                        "prd_id": metadata.get("artifact_id"),
                    },
                )
                documents.append(doc_features)

            # 3. 用户故事
            for idx, story in enumerate(prd.get('user_stories', [])):
                doc_story = Document(
                    page_content=f"""
用户故事 {idx + 1}:
角色: {story.get('role', '')}
动作: {story.get('action', '')}
价值: {story.get('benefit', '')}
                    """.strip(),
                    metadata={
                        **metadata,
                        "section": "user_story",
                        "story_index": idx,
                        "prd_id": metadata.get("artifact_id"),
                    },
                )
                documents.append(doc_story)

        return documents

    async def _index_documents(self, documents: list[Document]):
        """将文档索引到向量存储"""
        if not self.vector_store:
            logger.warning("No vector store configured, skipping indexing")
            return

        try:
            # 使用 LangChain 的 from_documents 方法
            self.vector_store.add_documents(documents)
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.7,
    ) -> list[dict]:
        """
        检索与查询相关的 PRD 内容

        Args:
            query: 查询文本
            top_k: 返回最相关的 K 个结果
            score_threshold: 相似度阈值（0-1）

        Returns:
            list[dict]: 检索结果列表，包含内容和元数据
        """
        if not self._initialized:
            await self.initialize()

        results = []

        if self.vector_store and self.embeddings:
            # 使用向量相似度检索
            try:
                docs = await self.vector_store.asimilarity_search_with_score(
                    query,
                    k=top_k,
                )

                for doc, score in docs:
                    if score >= score_threshold:
                        results.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "score": float(score),
                        })
            except Exception as e:
                logger.error(f"Vector search failed: {e}")

        # 如果向量检索失败或未配置，回退到简单的关键词匹配
        if not results:
            results = await self._keyword_search(query, top_k)

        logger.info(f"Retrieved {len(results)} relevant PRD sections for query: {query[:50]}")
        return results

    async def _keyword_search(self, query: str, top_k: int = 3) -> list[dict]:
        """简单的关键词搜索（回退方案）"""
        # 这里可以实现基于 TF-IDF 或 BM25 的关键词搜索
        # 为简化，暂时返回空结果
        logger.warning("Keyword search not implemented, returning empty results")
        return []

    def format_context(self, results: list[dict]) -> str:
        """
        将检索结果格式化为上下文字符串

        Args:
            results: 检索结果列表

        Returns:
            str: 格式化的上下文
        """
        if not results:
            return ""

        context_parts = ["## 📚 参考历史 PRD\n\n"]

        for idx, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            section = metadata.get("section", "unknown")
            created_at = metadata.get("created_at", "unknown")

            context_parts.append(f"### 参考 {idx} ({section})\n")
            context_parts.append(f"{result['content']}\n")
            context_parts.append(f"_来源: PRD #{metadata.get('prd_id')}, 创建于 {created_at}_\n\n")

        return "".join(context_parts)


# 全局单例
_prd_knowledge_base: Optional[PRDKnowledgeBase] = None


def get_prd_knowledge_base() -> PRDKnowledgeBase:
    """获取 PRD 知识库单例"""
    global _prd_knowledge_base
    if _prd_knowledge_base is None:
        _prd_knowledge_base = PRDKnowledgeBase()
    return _prd_knowledge_base


async def retrieve_similar_prds(
    query: str,
    top_k: int = 3,
    score_threshold: float = 0.7,
) -> str:
    """
    检索相似 PRD 并返回格式化的上下文

    Args:
        query: 查询文本
        top_k: 返回最相关的 K 个结果
        score_threshold: 相似度阈值

    Returns:
        str: 格式化的上下文字符串
    """
    kb = get_prd_knowledge_base()
    results = await kb.retrieve(query, top_k=top_k, score_threshold=score_threshold)
    return kb.format_context(results)


__all__ = [
    "PRDKnowledgeBase",
    "get_prd_knowledge_base",
    "retrieve_similar_prds",
]
