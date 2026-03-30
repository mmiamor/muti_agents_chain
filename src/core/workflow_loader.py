"""
工作流配置加载器 - 从文件加载工作流配置
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml
from pydantic import ValidationError

from src.models.workflow import WorkflowConfig, WorkflowTemplates
from src.utils.logger import setup_logger

logger = setup_logger("workflow_loader")


class WorkflowLoader:
    """工作流配置加载器"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化工作流加载器

        Args:
            config_dir: 配置文件目录，默认为项目根目录下的 workflows/
        """
        if config_dir is None:
            # 默认为项目根目录下的 workflows/ 目录
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "workflows"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 缓存已加载的配置
        self._cache: Dict[str, WorkflowConfig] = {}

    def load_template(self, template_name: str) -> WorkflowConfig:
        """
        加载预定义模板

        Args:
            template_name: 模板名称
                - full_pipeline: 完整流水线
                - rapid_prototype: 快速原型
                - design_only: 仅设计
                - backend_only: 仅后端
                - frontend_only: 仅前端

        Returns:
            工作流配置
        """
        templates = WorkflowTemplates()

        template_map = {
            "full_pipeline": templates.full_pipeline,
            "rapid_prototype": templates.rapid_prototype,
            "design_only": templates.design_only,
            "backend_only": templates.backend_only,
            "frontend_only": templates.frontend_only,
        }

        if template_name not in template_map:
            available = ", ".join(template_map.keys())
            raise ValueError(
                f"Unknown template: {template_name}. "
                f"Available templates: {available}"
            )

        return template_map[template_name]()

    def load_from_file(self, file_path: Union[str, Path]) -> WorkflowConfig:
        """
        从文件加载工作流配置

        Args:
            file_path: 配置文件路径（支持 .json 和 .yaml）

        Returns:
            工作流配置
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Workflow config not found: {file_path}")

        # 检查缓存
        cache_key = str(file_path)
        if cache_key in self._cache:
            logger.debug(f"从缓存加载配置: {file_path.name}")
            return self._cache[cache_key]

        # 根据文件扩展名选择解析器
        if file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif file_path.suffix in [".yaml", ".yml"]:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(
                f"Unsupported file format: {file_path.suffix}. "
                "Only .json and .yaml are supported."
            )

        # 解析配置
        try:
            config = WorkflowConfig(**data)
            self._cache[cache_key] = config
            logger.info(f"成功加载工作流配置: {file_path.name}")
            return config
        except ValidationError as e:
            logger.error(f"工作流配置验证失败: {e}")
            raise

    def load_from_dict(self, data: Dict) -> WorkflowConfig:
        """
        从字典加载工作流配置

        Args:
            data: 配置字典

        Returns:
            工作流配置
        """
        try:
            return WorkflowConfig(**data)
        except ValidationError as e:
            logger.error(f"工作流配置验证失败: {e}")
            raise

    def save_to_file(
        self,
        config: WorkflowConfig,
        file_path: Union[str, Path],
        format: str = "yaml",
    ) -> None:
        """
        保存工作流配置到文件

        Args:
            config: 工作流配置
            file_path: 文件路径
            format: 文件格式（yaml 或 json）
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换为字典
        data = config.model_dump()

        # 保存文件
        if format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format == "yaml":
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"工作流配置已保存: {file_path}")

        # 更新缓存
        self._cache[str(file_path)] = config

    def list_available_workflows(self) -> List[str]:
        """列出所有可用的工作流配置文件"""
        if not self.config_dir.exists():
            return []

        config_files = []
        for ext in ["*.json", "*.yaml", "*.yml"]:
            config_files.extend(self.config_dir.glob(ext))

        return [f.stem for f in config_files]

    def create_custom_workflow(
        self,
        name: str,
        agents: List[str],
        parallel: bool = False,
        skip_review: bool = False,
    ) -> WorkflowConfig:
        """
        创建自定义工作流

        Args:
            name: 工作流名称
            agents: Agent 列表
            parallel: 是否并行执行
            skip_review: 是否跳过审查

        Returns:
            工作流配置
        """
        from src.models.workflow import (
            AgentNodeConfig,
            ExecutionMode,
            ReviewConfig,
            ReviewStrategy,
            WorkflowStage,
        )

        agent_configs = [AgentNodeConfig(name=agent) for agent in agents]
        mode = ExecutionMode.PARALLEL if parallel else ExecutionMode.SEQUENTIAL

        review_config = ReviewConfig(
            enabled=not skip_review,
            strategy=ReviewStrategy.SKIP if skip_review else ReviewStrategy.AUTO,
        )

        stage = WorkflowStage(
            name="custom_stage",
            agents=agent_configs,
            mode=mode,
            review=review_config,
        )

        return WorkflowConfig(
            name=name,
            description=f"自定义工作流: {name}",
            stages=[stage],
        )


__all__ = ["WorkflowLoader"]
