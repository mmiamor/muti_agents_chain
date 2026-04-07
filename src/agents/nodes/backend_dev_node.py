"""Backend Dev Agent — LangGraph 节点函数"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from langchain_core.messages import AIMessage

from src.config import settings
from src.models.state import AgentState
from src.models.document_models import BackendCodeSpec
from src.agents.factory import create_llm, get_revision_count
from src.services.llm_service import _retry_with_backoff
from src.services.backend_codegen_service import BackendCodeGenerator
from src.services.code_locator_service import CodeFileOrganizer
from src.prompts.backend_dev_agent import SYSTEM_PROMPT
from src.utils.json_extract import extract_json

logger = logging.getLogger("backend_dev_node")


class BackendDevAgent:
    """Backend Dev Agent 实现"""

    name = "backend_dev_agent"
    role = "后端开发工程师"

    def __init__(self, llm=None):
        self.llm = llm
        if self.llm is None:
            self.llm = create_llm()

    async def run(self, state: AgentState) -> dict:
        """阅读 TRD，生成后端代码"""
        logger.info(f"[Backend Dev] processing, sender={state.get('sender', 'N/A')}")

        trd = state.get("trd")
        if not trd:
            logger.error("[Backend Dev] missing TRD")
            return {
                "sender": self.name,
                "messages": [AIMessage(content="Backend Dev: 缺少 TRD，无法生成后端代码。")],
            }

        if settings.NODE_DELAY > 0:
            await asyncio.sleep(settings.NODE_DELAY)

        # ── 使用精确的代码生成器 ────────────────────────────────────
        try:
            # 初始化代码生成器
            code_generator = BackendCodeGenerator()

            # 初始化文件组织器
            file_organizer = CodeFileOrganizer(project_type="backend")

            # 生成代码结构
            locations = file_organizer.organize_backend_code(trd)

            # 检测冲突
            conflicts = file_organizer.resolver.detect_conflicts(locations)
            if conflicts:
                logger.warning(f"[Backend Dev] Detected path conflicts: {list(conflicts.keys())}")

            # 生成代码
            output_dir = "./output"
            code_spec = code_generator.generate_from_trd(trd, output_dir)

            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            logger.info(f"[Backend Dev] generated {len(code_spec.files)} files")
            logger.info(f"[Backend Dev] project structure:\n{code_spec.project_structure}")

            return {
                "backend_code": code_spec,
                "sender": self.name,
                "messages": [
                    AIMessage(
                        content=(
                            f"Backend Dev 已生成后端代码:\n"
                            f"文件数: {len(code_spec.files)}\n"
                            f"技术栈: {trd.tech_stack.backend}\n"
                            f"依赖: {code_spec.dependencies}\n\n"
                            f"启动命令:\n" + "\n".join(f"  {cmd}" for cmd in code_spec.setup_commands)
                        )
                    )
                ],
            }

        except Exception as e:
            logger.error(f"[Backend Dev] code generation failed: {e}")

            # 降级到原始 LLM 生成方式
            return await self._fallback_generate(state, trd)

    async def _fallback_generate(self, state: AgentState, trd) -> dict:
        """降级生成方案（使用原始 LLM）"""
        # 审查反馈上下文
        review_context = ""
        latest_review = state.get("latest_review")
        revision_count = get_revision_count(state, self.name)
        if latest_review and latest_review.status == "REJECTED":
            review_context = (
                f"\n\n审查员反馈（第 {revision_count} 次修改）:\n"
                f"{latest_review.comments}\n请据此修改后端代码。"
            )

        context = (
            f"根据以下 TRD 生成后端代码：\n\n"
            f"```json\n{trd.model_dump_json(indent=2)}\n```"
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
        logger.debug(f"[Backend Dev] fallback raw response: {content[:200]}")

        data = extract_json(content)
        code_spec = BackendCodeSpec(**data)

        logger.info(f"[Backend Dev] fallback generated {len(code_spec.files)} files")

        return {
            "backend_code": code_spec,
            "sender": self.name,
            "messages": [
                AIMessage(
                    content=(
                        f"Backend Dev 已生成后端代码:\n"
                        f"文件数: {len(code_spec.files)}\n"
                        f"依赖: {code_spec.dependencies}"
                    )
                )
            ],
        }


_backend_dev_agent: BackendDevAgent | None = None


def get_backend_dev_agent() -> BackendDevAgent:
    global _backend_dev_agent
    if _backend_dev_agent is None:
        _backend_dev_agent = BackendDevAgent()
    return _backend_dev_agent


async def backend_dev_node(state: AgentState) -> dict:
    return await get_backend_dev_agent().run(state)
