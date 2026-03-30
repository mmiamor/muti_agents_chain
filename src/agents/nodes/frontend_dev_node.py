"""Frontend Dev Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import FrontendCodeSpec
from src.agents.factory import create_llm, get_revision_count
from src.services.llm_service import _retry_with_backoff
from src.prompts.frontend_dev_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("frontend_dev_node")


class FrontendDevAgent:
    """Frontend Dev Agent 实现"""

    name = "frontend_dev_agent"
    role = "前端开发工程师"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()

    async def run(self, state: AgentState) -> dict:
        """阅读 TRD + DesignDocument，生成前端代码"""
        logger.info(f"[Frontend Dev] processing, sender={state.get('sender', 'N/A')}")

        trd = state.get("trd")
        design = state.get("design_doc")

        if not trd or not design:
            logger.error("[Frontend Dev] missing TRD or DesignDocument")
            return {
                "sender": self.name,
                "messages": [AIMessage(content="Frontend Dev: 缺少 TRD 或 DesignDocument，无法生成前端代码。")],
            }

        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)

        # 审查反馈上下文
        review_context = ""
        latest_review = state.get("latest_review")
        revision_count = get_revision_count(state, self.name)
        if latest_review and latest_review.status == "REJECTED":
            review_context = (
                f"\n\n审查员反馈（第 {revision_count} 次修改）:\n"
                f"{latest_review.comments}\n请据此修改前端代码。"
            )

        context = (
            f"根据以下 TRD 和 DesignDocument 生成前端代码：\n\n"
            f"### TRD\n```json\n{trd.model_dump_json(indent=2)}\n```\n\n"
            f"### DesignDocument\n```json\n{design.model_dump_json(indent=2)}\n```"
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + review_context},
            {"role": "user", "content": context},
        ]

        response = await _retry_with_backoff(
            coro_factory=lambda: self.llm.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=messages,
                temperature=0,
            ),
            max_retries=self.llm.max_retries,
            base_delay=self.llm.base_delay,
        )

        content = response.choices[0].message.content
        logger.debug(f"[Frontend Dev] raw response: {content[:200]}")

        data = extract_json(content)
        code_spec = FrontendCodeSpec(**data)

        logger.info(f"[Frontend Dev] generated {len(code_spec.files)} files")

        return {
            "frontend_code": code_spec,
            "sender": self.name,
            "messages": [
                AIMessage(
                    content=(
                        f"Frontend Dev 已生成前端代码:\n"
                        f"文件数: {len(code_spec.files)}\n"
                        f"依赖: {code_spec.dependencies}"
                    )
                )
            ],
        }


_frontend_dev_agent: FrontendDevAgent | None = None


def get_frontend_dev_agent() -> FrontendDevAgent:
    global _frontend_dev_agent
    if _frontend_dev_agent is None:
        _frontend_dev_agent = FrontendDevAgent()
    return _frontend_dev_agent


async def frontend_dev_node(state: AgentState) -> dict:
    return await get_frontend_dev_agent().run(state)
