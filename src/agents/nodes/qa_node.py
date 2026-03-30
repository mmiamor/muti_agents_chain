"""QA Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import QAReport
from src.agents.factory import create_llm, get_revision_count
from src.services.llm_service import _retry_with_backoff
from src.prompts.qa_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("qa_node")


class QAAgent:
    """QA Agent 实现"""

    name = "qa_agent"
    role = "质量保障专家"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()

    async def run(self, state: AgentState) -> dict:
        """阅读全部产出物，生成 QA 报告"""
        logger.info(f"[QA] processing, sender={state.get('sender', 'N/A')}")

        prd = state.get("prd")
        trd = state.get("trd")
        design = state.get("design_doc")
        backend = state.get("backend_code")
        frontend = state.get("frontend_code")

        if not prd or not trd:
            logger.error("[QA] missing PRD or TRD")
            return {
                "sender": self.name,
                "messages": [AIMessage(content="QA: 缺少 PRD 或 TRD，无法生成质量报告。")],
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
                f"{latest_review.comments}\n请据此修改 QA 报告。"
            )

        # 构建上下文：所有可用产出物
        parts = []
        parts.append(f"### PRD\n```json\n{prd.model_dump_json(indent=2)}\n```")
        parts.append(f"### TRD\n```json\n{trd.model_dump_json(indent=2)}\n```")
        if design:
            parts.append(f"### DesignDocument\n```json\n{design.model_dump_json(indent=2)}\n```")
        if backend:
            parts.append(f"### BackendCode\n```json\n{backend.model_dump_json(indent=2)}\n```")
        if frontend:
            parts.append(f"### FrontendCode\n```json\n{frontend.model_dump_json(indent=2)}\n```")

        context = f"根据以下全部产出物进行质量评估和测试计划设计：\n\n" + "\n\n".join(parts)

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
        logger.debug(f"[QA] raw response: {content[:200]}")

        data = extract_json(content)
        report = QAReport(**data)

        high_count = sum(1 for i in report.potential_issues if i.severity == "high")
        logger.info(
            f"[QA] generated report: score={report.quality_score}, "
            f"tests={len(report.test_plan)}, issues={len(report.potential_issues)} (high={high_count})"
        )

        return {
            "qa_report": report,
            "sender": self.name,
            "messages": [
                AIMessage(
                    content=(
                        f"QA 质量报告:\n"
                        f"质量评分: {report.quality_score}/10\n"
                        f"测试用例: {len(report.test_plan)} 个\n"
                        f"潜在问题: {len(report.potential_issues)} 个 (高风险: {high_count})\n"
                        f"总结: {report.summary[:100]}"
                    )
                )
            ],
        }


_qa_agent: QAAgent | None = None


def get_qa_agent() -> QAAgent:
    global _qa_agent
    if _qa_agent is None:
        _qa_agent = QAAgent()
    return _qa_agent


async def qa_node(state: AgentState) -> dict:
    return await get_qa_agent().run(state)
