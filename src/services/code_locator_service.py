"""
代码文件定位系统 - 精确的文件路径解析和映射

确保生成的代码文件位置准确，支持增量更新和文件冲突检测
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("code_locator")


class FileRole(str, Enum):
    """文件角色分类"""
    # 后端文件角色
    MODEL = "model"  # 数据模型
    CONTROLLER = "controller"  # API 控制器
    SERVICE = "service"  # 业务逻辑
    ROUTE = "route"  # 路由配置
    MIDDLEWARE = "middleware"  # 中间件
    CONFIG = "config"  # 配置文件
    UTIL = "util"  # 工具函数

    # 前端文件角色
    COMPONENT = "component"  # UI 组件
    PAGE = "page"  # 页面
    HOOK = "hook"  # 自定义 Hook
    STORE = "store"  # 状态管理
    API = "api"  # API 调用
    TYPE = "type"  # 类型定义
    STYLE = "style"  # 样式文件
    ASSET = "asset"  # 静态资源


class FileType(str, Enum):
    """文件类型"""
    PYTHON = ".py"
    TYPESCRIPT = ".ts"
    TSX = ".tsx"
    JAVASCRIPT = ".js"
    JSX = ".jsx"
    CSS = ".css"
    SCSS = ".scss"
    JSON = ".json"
    YAML = ".yaml"
    YML = ".yml"
    MD = ".md"
    TXT = ".txt"


@dataclass
class FileLocation:
    """文件位置信息"""
    path: str  # 完整路径
    relative_path: str  # 相对于项目根目录的路径
    role: FileRole  # 文件角色
    file_type: FileType  # 文件类型
    module: str  # 所属模块
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他文件
    is_new: bool = True  # 是否为新文件


@dataclass
class PathMapping:
    """路径映射规则"""
    pattern: str  # 匹配模式（正则表达式）
    template: str  # 路径模板
    role: FileRole  # 文件角色
    description: str  # 说明


class CodePathResolver:
    """代码路径解析器"""

    # 后端路径映射规则（FastAPI）
    BACKEND_PATH_RULES: list[PathMapping] = [
        PathMapping(
            pattern=r"^app\.models\.(.+)$",
            template="app/models/{module}.py",
            role=FileRole.MODEL,
            description="数据模型文件",
        ),
        PathMapping(
            pattern=r"^app\.api\.v1\.endpoints\.(.+)$",
            template="app/api/v1/endpoints/{module}.py",
            role=FileRole.CONTROLLER,
            description="API 端点文件",
        ),
        PathMapping(
            pattern=r"^app\.services\.(.+)$",
            template="app/services/{module}_service.py",
            role=FileRole.SERVICE,
            description="业务逻辑服务",
        ),
        PathMapping(
            pattern=r"^app\.core\.(.+)$",
            template="app/core/{module}.py",
            role=FileRole.CONFIG,
            description="核心配置文件",
        ),
        PathMapping(
            pattern=r"^app\.db\.(.+)$",
            template="app/db/{module}.py",
            role=FileRole.CONFIG,
            description="数据库配置",
        ),
    ]

    # 前端路径映射规则（React）
    FRONTEND_PATH_RULES: list[PathMapping] = [
        PathMapping(
            pattern=r"^pages\.(.+)$",
            template="src/pages/{module}.tsx",
            role=FileRole.PAGE,
            description="页面组件",
        ),
        PathMapping(
            pattern=r"^components\.(.+)$",
            template="src/components/{module}.tsx",
            role=FileRole.COMPONENT,
            description="通用组件",
        ),
        PathMapping(
            pattern=r"^services\.(.+)$",
            template="src/services/{module}.ts",
            role=FileRole.API,
            description="API 服务",
        ),
        PathMapping(
            pattern=r"^hooks\.(.+)$",
            template="src/hooks/{module}.ts",
            role=FileRole.HOOK,
            description="自定义 Hook",
        ),
        PathMapping(
            pattern=r"^types\.(.+)$",
            template="src/types/{module}.ts",
            role=FileRole.TYPE,
            description="类型定义",
        ),
        PathMapping(
            pattern=r"^utils\.(.+)$",
            template="src/utils/{module}.ts",
            role=FileRole.UTIL,
            description="工具函数",
        ),
        PathMapping(
            pattern=r"^styles\.(.+)$",
            template="src/styles/{module}.css",
            role=FileRole.STYLE,
            description="样式文件",
        ),
    ]

    def __init__(self, project_type: str = "backend"):
        """
        初始化路径解析器

        Args:
            project_type: 项目类型（backend/frontend）
        """
        self.project_type = project_type
        self.rules = self.BACKEND_PATH_RULES if project_type == "backend" else self.FRONTEND_PATH_RULES

    def resolve(
        self,
        module_name: str,
        role: FileRole | None = None,
        base_path: str = "./output"
    ) -> FileLocation:
        """
        解析文件路径

        Args:
            module_name: 模块名称（如 user, item, auth）
            role: 文件角色（可选）
            base_path: 基础路径

        Returns:
            FileLocation: 文件位置信息
        """
        # 查找匹配的路径规则
        for rule in self.rules:
            if role and rule.role != role:
                continue

            # 构建完整路径
            full_path = rule.template.format(
                module=self._normalize_module_name(module_name),
                role=role.value if role else "common",
            )

            # 确定文件类型
            file_type = self._get_file_type_from_path(full_path)

            # 构建相对路径
            relative_path = self._make_relative(base_path, full_path)

            return FileLocation(
                path=full_path,
                relative_path=relative_path,
                role=rule.role,
                file_type=file_type,
                module=module_name,
            )

        # 默认路径
        default_path = f"{base_path}/{module_name}.py"
        return FileLocation(
            path=default_path,
            relative_path=f"{module_name}.py",
            role=role or FileRole.UTIL,
            file_type=FileType.PYTHON,
            module=module_name,
        )

    def _normalize_module_name(self, name: str) -> str:
        """规范化模块名称"""
        # 转换为小写，替换空格和特殊字符
        normalized = name.lower().replace("-", "_").replace(" ", "_")
        # 移除非字母数字字符
        normalized = re.sub(r"[^a-z0-9_]", "", normalized)
        return normalized

    def _get_file_type_from_path(self, path: str) -> FileType:
        """从路径获取文件类型"""
        for ft in FileType:
            if path.endswith(ft.value):
                return ft
        return FileType.TXT

    def _make_relative(self, base_path: str, full_path: str) -> str:
        """构建相对路径"""
        try:
            base = Path(base_path)
            full = Path(full_path)
            return str(full.relative_to(base))
        except ValueError:
            return full_path

    def detect_conflicts(self, locations: list[FileLocation]) -> dict[str, list[FileLocation]]:
        """
        检测文件路径冲突

        Args:
            locations: 文件位置列表

        Returns:
            dict: 冲突映射（路径 -> 文件列表）
        """
        conflicts: dict[str, list[FileLocation]] = {}

        for location in locations:
            if location.path not in conflicts:
                conflicts[location.path] = []
            conflicts[location.path].append(location)

        # 只保留有冲突的路径
        return {k: v for k, v in conflicts.items() if len(v) > 1}

    def validate_dependencies(
        self,
        locations: list[FileLocation],
        existing_files: list[str]
    ) -> list[tuple[FileLocation, str]]:
        """
        验证文件依赖

        Args:
            locations: 文件位置列表
            existing_files: 已存在的文件列表

        Returns:
            list: 缺失的依赖项
        """
        missing = []

        for location in locations:
            for dep in location.dependencies:
                dep_path = Path(location.path).parent / dep
                if str(dep_path) not in existing_files:
                    missing.append((location, str(dep_path)))

        return missing


class CodeFileOrganizer:
    """代码文件组织器 - 管理文件结构和依赖关系"""

    def __init__(self, project_type: str = "backend"):
        self.resolver = CodePathResolver(project_type)
        self.project_type = project_type

    def organize_backend_code(self, trd: Any) -> list[FileLocation]:
        """
        组织后端代码结构

        Args:
            trd: 技术设计文档

        Returns:
            list[FileLocation]: 文件位置列表
        """
        locations = []

        # 1. 核心配置文件
        for config in ["main", "config", "security"]:
            locations.append(self.resolver.resolve(
                f"app.core.{config}",
                FileRole.CONFIG,
            ))

        # 2. 数据库文件
        for db in ["session", "base"]:
            locations.append(self.resolver.resolve(
                f"app.db.{db}",
                FileRole.CONFIG,
            ))

        # 3. 根据 API 端点生成文件
        for endpoint in getattr(trd, "api_endpoints", []):
            # 从路径提取模块名
            module = self._extract_module_from_path(endpoint.path)
            locations.append(self.resolver.resolve(
                f"app.api.v1.endpoints.{module}",
                FileRole.CONTROLLER,
            ))

            # 生成对应的服务
            locations.append(self.resolver.resolve(
                f"app.services.{module}",
                FileRole.SERVICE,
            ))

        # 4. 数据模型
        locations.append(self.resolver.resolve(
            "app.models",
            FileRole.MODEL,
        ))

        return locations

    def organize_frontend_code(self, design: Any) -> list[FileLocation]:
        """
        组织前端代码结构

        Args:
            design: 设计文档

        Returns:
            list[FileLocation]: 文件位置列表
        """
        locations = []

        # 1. 核心文件
        for core in ["main", "App"]:
            locations.append(self.resolver.resolve(
                core,
                FileRole.PAGE if core == "App" else FileRole.CONFIG,
            ))

        # 2. 页面组件
        for page_spec in getattr(design, "page_specs", []):
            page_name = page_spec.page_name.replace(" ", "")
            locations.append(self.resolver.resolve(
                f"pages.{page_name}",
                FileRole.PAGE,
            ))

        # 3. 布局组件
        for layout in ["Header", "Sidebar", "Footer"]:
            locations.append(self.resolver.resolve(
                f"components.{layout}",
                FileRole.COMPONENT,
            ))

        # 4. 服务层
        locations.append(self.resolver.resolve(
            "services.api",
            FileRole.API,
        ))

        # 5. 类型定义
        locations.append(self.resolver.resolve(
            "types",
            FileRole.TYPE,
        ))

        # 6. 工具函数
        locations.append(self.resolver.resolve(
            "utils.request",
            FileRole.UTIL,
        ))

        return locations

    def _extract_module_from_path(self, path: str) -> str:
        """从 API 路径提取模块名"""
        # 移除开头的 / 和结尾的 /s
        clean_path = path.strip("/")

        # 分割路径，取第一段作为模块名
        parts = clean_path.split("/")
        if parts:
            return parts[0].replace("-", "_")

        return "default"

    def generate_structure_report(self, locations: list[FileLocation]) -> str:
        """生成结构报告"""
        lines = [
            "# 代码文件结构报告\n",
            "## 文件统计\n",
            f"- 总文件数: {len(locations)}",
        ]

        # 按角色分组
        by_role: dict[FileRole, list[FileLocation]] = {}
        for loc in locations:
            if loc.role not in by_role:
                by_role[loc.role] = []
            by_role[loc.role].append(loc)

        lines.append("\n## 按角色分类\n")
        for role, files in sorted(by_role.items()):
            lines.append(f"\n### {role.value} ({len(files)} 个文件)\n")
            for file in files:
                lines.append(f"- `{file.relative_path}`")

        lines.append("\n## 完整路径\n")
        for loc in locations:
            lines.append(f"- {loc.path}")

        return "\n".join(lines)


__all__ = [
    "FileRole",
    "FileType",
    "FileLocation",
    "PathMapping",
    "CodePathResolver",
    "CodeFileOrganizer",
]
