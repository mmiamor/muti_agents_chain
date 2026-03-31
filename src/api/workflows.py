"""
工作流管理 API - 提供工作流的 CRUD 操作和执行接口
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from src.core.workflow_loader import WorkflowLoader
from src.core.workflow_engine import WorkflowEngine
from src.models.workflow import WorkflowConfig, WorkflowTemplates
from src.models.state import AgentState
from src.utils.logger import setup_logger

logger = setup_logger("workflow_api")

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# 全局工作流加载器
loader = WorkflowLoader()

# 执行中的工作流存储
executing_workflows: Dict[str, WorkflowEngine] = {}


# ==================== Request/Response 模型 ====================

class WorkflowCreateRequest(BaseModel):
    """创建工作流请求"""
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    agents: List[str] = Field(..., description="Agent 列表")
    parallel: bool = Field(default=False, description="是否并行执行")
    skip_review: bool = Field(default=False, description="是否跳过审查")
    save_as_file: bool = Field(default=True, description="是否保存为文件")


class WorkflowExecuteRequest(BaseModel):
    """执行工作流请求"""
    message: str = Field(..., description="用户需求描述")
    stop_at_stage: Optional[str] = Field(None, description="停止阶段（用于调试）")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="额外参数")


class WorkflowResponse(BaseModel):
    """工作流响应"""
    name: str
    description: Optional[str]
    version: str
    stage_count: int
    agents: List[str]
    execution_modes: List[str]


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    workflow_name: str
    execution_id: str
    status: str  # running, completed, failed, cancelled
    current_stage: Optional[str]
    completed_stages: int
    total_stages: int
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]


class TemplateResponse(BaseModel):
    """模板响应"""
    name: str
    description: str
    stage_count: int


# ==================== API 端点 ====================

@router.get("/", response_model=List[str])
async def list_workflows():
    """
    列出所有可用的工作流

    Returns:
        工作流名称列表
    """
    try:
        # 列出预定义模板
        templates = [
            "full_pipeline",
            "rapid_prototype",
            "design_only",
            "backend_only",
            "frontend_only",
        ]

        # 列出配置文件
        config_files = loader.list_available_workflows()

        # 合并并去重
        all_workflows = sorted(set(templates + config_files))

        return all_workflows

    except Exception as e:
        logger.error(f"列出工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出工作流失败: {str(e)}"
        )


@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates():
    """
    列出所有预定义模板

    Returns:
        模板列表
    """
    try:
        templates = WorkflowTemplates()

        template_info = [
            {
                "name": "full_pipeline",
                "description": "完整的软件开发流水线",
                "stage_count": len(templates.full_pipeline().stages),
            },
            {
                "name": "rapid_prototype",
                "description": "快速原型开发（无审查）",
                "stage_count": len(templates.rapid_prototype().stages),
            },
            {
                "name": "design_only",
                "description": "仅设计阶段",
                "stage_count": len(templates.design_only().stages),
            },
            {
                "name": "backend_only",
                "description": "仅后端开发",
                "stage_count": len(templates.backend_only().stages),
            },
            {
                "name": "frontend_only",
                "description": "仅前端开发",
                "stage_count": len(templates.frontend_only().stages),
            },
        ]

        return [TemplateResponse(**info) for info in template_info]

    except Exception as e:
        logger.error(f"列出模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出模板失败: {str(e)}"
        )


@router.get("/{workflow_name}", response_model=WorkflowResponse)
async def get_workflow(workflow_name: str):
    """
    获取工作流详情

    Args:
        workflow_name: 工作流名称

    Returns:
        工作流详情
    """
    try:
        # 尝试加载模板
        try:
            workflow = loader.load_template(workflow_name)
        except ValueError:
            # 尝试加载文件
            workflow = loader.load_from_file(f"workflows/{workflow_name}.yaml")

        # 提取所有 Agent
        all_agents = []
        execution_modes = []

        for stage in workflow.stages:
            for agent in stage.agents:
                if agent.name not in all_agents:
                    all_agents.append(agent.name)
            if stage.mode.value not in execution_modes:
                execution_modes.append(stage.mode.value)

        return WorkflowResponse(
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            stage_count=len(workflow.stages),
            agents=all_agents,
            execution_modes=execution_modes,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_name}"
        )
    except Exception as e:
        logger.error(f"获取工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流失败: {str(e)}"
        )


@router.post("/", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(request: WorkflowCreateRequest):
    """
    创建自定义工作流

    Args:
        request: 工作流创建请求

    Returns:
        创建的工作流详情
    """
    try:
        # 创建工作流
        workflow = loader.create_custom_workflow(
            name=request.name,
            agents=request.agents,
            parallel=request.parallel,
            skip_review=request.skip_review,
        )

        # 添加描述
        if request.description:
            workflow.description = request.description

        # 保存到文件
        if request.save_as_file:
            output_path = f"workflows/{request.name}.yaml"
            loader.save_to_file(workflow, output_path, format="yaml")
            logger.info(f"工作流已保存: {output_path}")

        # 提取所有 Agent
        all_agents = request.agents
        execution_modes = ["parallel" if request.parallel else "sequential"]

        return WorkflowResponse(
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            stage_count=len(workflow.stages),
            agents=all_agents,
            execution_modes=execution_modes,
        )

    except Exception as e:
        logger.error(f"创建工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建工作流失败: {str(e)}"
        )


@router.post("/{workflow_name}/execute", response_model=WorkflowStatusResponse)
async def execute_workflow(
    workflow_name: str,
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
):
    """
    执行工作流

    Args:
        workflow_name: 工作流名称
        request: 执行请求
        background_tasks: 后台任务

    Returns:
        执行状态
    """
    try:
        # 生成执行 ID
        execution_id = str(uuid.uuid4())

        # 加载工作流
        try:
            workflow = loader.load_template(workflow_name)
        except ValueError:
            workflow = loader.load_from_file(f"workflows/{workflow_name}.yaml")

        # 创建初始状态
        initial_state = AgentState(
            messages=[{"role": "user", "content": request.message}],
            sender="user",
            **request.parameters,
        )

        # 创建工作流引擎
        engine = WorkflowEngine(workflow)

        # 存储引擎
        executing_workflows[execution_id] = engine

        # 在后台执行工作流
        background_tasks.add_task(
            _execute_workflow_background,
            execution_id,
            engine,
            initial_state,
            request.stop_at_stage,
        )

        return WorkflowStatusResponse(
            workflow_name=workflow_name,
            execution_id=execution_id,
            status="running",
            current_stage=None,
            completed_stages=0,
            total_stages=len(workflow.stages),
            started_at=datetime.now(),
            completed_at=None,
            error=None,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"工作流不存在: {workflow_name}"
        )
    except Exception as e:
        logger.error(f"执行工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行工作流失败: {str(e)}"
        )


async def _execute_workflow_background(
    execution_id: str,
    engine: WorkflowEngine,
    initial_state: AgentState,
    stop_at_stage: Optional[str],
):
    """
    后台执行工作流

    Args:
        execution_id: 执行 ID
        engine: 工作流引擎
        initial_state: 初始状态
        stop_at_stage: 停止阶段
    """
    try:
        logger.info(f"开始执行工作流: {execution_id}")

        # 执行工作流
        await engine.execute(initial_state, stop_at_stage=stop_at_stage)

        logger.info(f"工作流执行完成: {execution_id}")

    except Exception as e:
        logger.error(f"工作流执行失败: {execution_id}, 错误: {e}")
        # 存储错误信息
        engine.execution_error = str(e)


@router.get("/{workflow_name}/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_name: str, execution_id: str):
    """
    查询工作流执行状态

    Args:
        workflow_name: 工作流名称
        execution_id: 执行 ID

    Returns:
        执行状态
    """
    try:
        if execution_id not in executing_workflows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"执行不存在: {execution_id}"
            )

        engine = executing_workflows[execution_id]
        summary = engine.get_execution_summary()

        # 确定状态
        if hasattr(engine, 'execution_error'):
            status_value = "failed"
            error = engine.execution_error
        elif summary["completed_stages"] >= summary["total_stages"]:
            status_value = "completed"
            error = None
        else:
            status_value = "running"
            error = None

        # 获取当前阶段
        current_stage = None
        if engine.execution_history:
            current_stage = engine.execution_history[-1]["stage"]

        return WorkflowStatusResponse(
            workflow_name=workflow_name,
            execution_id=execution_id,
            status=status_value,
            current_stage=current_stage,
            completed_stages=summary["completed_stages"],
            total_stages=summary["total_stages"],
            started_at=datetime.now(),  # TODO: 存储实际开始时间
            completed_at=datetime.now() if status_value == "completed" else None,
            error=error,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工作流状态失败: {str(e)}"
        )


@router.delete("/{workflow_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(workflow_name: str):
    """
    删除工作流

    Args:
        workflow_name: 工作流名称

    Returns:
        No Content
    """
    try:
        # 只能删除自定义工作流（文件形式），不能删除模板
        try:
            loader.load_template(workflow_name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不能删除预定义模板: {workflow_name}"
            )
        except ValueError:
            pass

        # 尝试删除文件
        import os
        file_path = f"workflows/{workflow_name}.yaml"

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"工作流已删除: {file_path}")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工作流不存在: {workflow_name}"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工作流失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工作流失败: {str(e)}"
        )


__all__ = ["router"]
