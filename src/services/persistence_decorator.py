"""
Agent 持久化装饰器 - 自动保存Agent执行结果到数据库
"""
from functools import wraps
from typing import Callable

from src.services.persistence_service import get_persistence_service


def with_persistence(
    save_artifact: bool = True,
    save_review: bool = True,
    save_messages: bool = False,
):
    """
    Agent 持久化装饰器 - 自动保存Agent执行结果

    Args:
        save_artifact: 是否保存产出物
        save_review: 是否保存审查结果
        save_messages: 是否保存消息历史
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(state, *args, **kwargs):
            # 执行原始Agent逻辑
            result = await func(state, *args, **kwargs)

            # 获取必要信息
            thread_id = state.get("thread_id", "unknown")
            sender = result.get("sender", "unknown")

            if save_artifact:
                # 保存产出物
                persistence = get_persistence_service()

                # 根据不同的Agent类型保存不同的产出物
                if result.get("prd"):
                    await persistence.save_artifact(
                        thread_id,
                        "pm_agent",
                        "prd",
                        result["prd"],
                        is_approved=result.get("latest_review", {}).get("status") == "APPROVED"
                    )

                if result.get("trd"):
                    await persistence.save_artifact(
                        thread_id,
                        "architect_agent",
                        "trd",
                        result["trd"],
                        is_approved=result.get("latest_review", {}).get("status") == "APPROVED"
                    )

                if result.get("design_doc"):
                    await persistence.save_artifact(
                        thread_id,
                        "design_agent",
                        "design_doc",
                        result["design_doc"],
                        is_approved=result.get("latest_review", {}).get("status") == "APPROVED"
                    )

                if result.get("backend_code"):
                    await persistence.save_artifact(
                        thread_id,
                        "backend_dev_agent",
                        "backend_code",
                        result["backend_code"],
                        is_approved=result.get("latest_review", {}).get("status") == "APPROVED"
                    )

                if result.get("frontend_code"):
                    await persistence.save_artifact(
                        thread_id,
                        "frontend_dev_agent",
                        "frontend_code",
                        result["frontend_code"],
                        is_approved=result.get("latest_review", {}).get("status") == "APPROVED"
                    )

                if result.get("qa_report"):
                    await persistence.save_artifact(
                        thread_id,
                        "qa_agent",
                        "qa_report",
                        result["qa_report"],
                        is_approved=result.get("latest_review", {}).get("status") == "APPROVED"
                    )

            if save_review and result.get("latest_review"):
                # 保存审查结果
                persistence = get_persistence_service()
                review = result["latest_review"]
                revision_counts = result.get("revision_counts", {})
                revision_count = revision_counts.get(sender, 0)

                await persistence.save_review(
                    thread_id,
                    sender,
                    review,
                    revision_count
                )

            if save_messages and result.get("messages"):
                # 保存消息历史（只保存新增的）
                persistence = get_persistence_service()
                for message in result["messages"][-1:]:  # 只保存最新的消息
                    from src.utils.helpers import message_to_dict
                    msg_dict = message_to_dict(message)
                    await persistence.save_message(
                        thread_id,
                        msg_dict.get("role", "unknown"),
                        msg_dict.get("content", ""),
                        msg_dict.get("name")
                    )

            return result

        return wrapper

    return decorator


async def create_thread_on_start(state):
    """在流程开始时创建线程记录"""
    thread_id = state.get("thread_id") or "default"
    user_message = ""

    # 从messages中提取用户消息
    messages = state.get("messages", [])
    for msg in messages:
        if hasattr(msg, "type") and msg.type == "human":
            user_message = msg.content
            break

    persistence = get_persistence_service()
    await persistence.create_thread(
        thread_id=thread_id,
        user_message=user_message,
        current_phase=state.get("current_phase", "requirement_gathering")
    )

    return state


async def update_thread_completion(state):
    """在流程完成时更新线程状态"""
    thread_id = state.get("thread_id")
    if not thread_id:
        return

    persistence = get_persistence_service()

    # 确定最终状态
    final_status = "completed"
    if state.get("latest_review", {}).get("status") == "REJECTED":
        final_status = "failed"

    await persistence.update_thread_status(
        thread_id=thread_id,
        status=final_status,
        current_phase=state.get("current_phase")
    )