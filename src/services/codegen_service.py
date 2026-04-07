"""
项目结构配置系统 - 定义前后端项目的标准目录结构

支持多种技术栈的项目结构定义，确保生成的代码文件位置准确
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from enum import Enum


class TechStack(str, Enum):
    """支持的技术栈"""
    # 后端技术栈
    PYTHON_FASTAPI = "python_fastapi"
    PYTHON_FLASK = "python_flask"
    NODE_EXPRESS = "node_express"
    NODE_NESTJS = "node_nestjs"
    GO_GIN = "go_gin"
    JAVA_SPRING = "java_spring"

    # 前端技术栈
    REACT_TS = "react_ts"
    REACT_JS = "react_js"
    VUE_TS = "vue_ts"
    VUE_JS = "vue_js"
    NEXT_JS = "next_js"
    NUXT_TS = "nuxt_ts"


@dataclass
class FileTemplate:
    """文件模板定义"""
    path: str  # 文件路径（相对于项目根目录）
    content_type: Literal["model", "controller", "service", "route", "component", "page", "util", "config"]
    description: str  # 文件用途说明
    required: bool = True  # 是否必需


@dataclass
class ProjectStructure:
    """项目结构定义"""
    name: str
    tech_stack: TechStack
    description: str
    base_path: str  # 基础路径（生成代码的根目录）
    directories: list[str] = field(default_factory=list)  # 需要创建的目录
    file_templates: list[FileTemplate] = field(default_factory=list)  # 文件模板
    dependencies: list[str] = field(default_factory=list)  # 核心依赖
    dev_dependencies: list[str] = field(default_factory=list)  # 开发依赖
    config_files: dict[str, str] = field(default_factory=dict)  # 配置文件


# ==================== 后端项目结构 ====================

FASTAPI_STRUCTURE = ProjectStructure(
    name="FastAPI Backend",
    tech_stack=TechStack.PYTHON_FASTAPI,
    description="Python FastAPI 后端项目标准结构",
    base_path="backend",
    directories=[
        "backend/app",
        "backend/app/api",
        "backend/app/api/v1",
        "backend/app/api/v1/endpoints",
        "backend/app/core",
        "backend/app/models",
        "backend/app/schemas",
        "backend/app/services",
        "backend/app/db",
        "backend/tests",
        "backend/tests/api",
        "backend/tests/services",
    ],
    file_templates=[
        FileTemplate("backend/app/main.py", "config", "应用入口"),
        FileTemplate("backend/app/core/config.py", "config", "配置管理"),
        FileTemplate("backend/app/core/security.py", "util", "安全相关工具"),
        FileTemplate("backend/app/db/session.py", "config", "数据库会话"),
        FileTemplate("backend/app/db/base.py", "model", "数据库基类"),
        FileTemplate("backend/app/models/__init__.py", "model", "模型模块"),
        FileTemplate("backend/app/schemas/__init__.py", "model", "Schema模块"),
        FileTemplate("backend/app/api/v1/endpoints/__init__.py", "controller", "API端点"),
        FileTemplate("backend/app/services/__init__.py", "service", "业务逻辑层"),
    ],
    dependencies=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "alembic>=1.12.0",
    ],
    dev_dependencies=[
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "httpx>=0.25.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.5.0",
    ],
    config_files={
        "requirements.txt": "\n".join([
            "# Backend dependencies",
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "sqlalchemy>=2.0.0",
            "pydantic>=2.0.0",
        ]),
        ".env.example": "OPENAI_API_KEY=\nDATABASE_URL=\n",
    }
)

NESTJS_STRUCTURE = ProjectStructure(
    name="NestJS Backend",
    tech_stack=TechStack.NODE_NESTJS,
    description="Node.js NestJS 后端项目标准结构",
    base_path="backend",
    directories=[
        "backend/src",
        "backend/src/modules",
        "backend/src/common",
        "backend/src/config",
        "backend/src/database",
        "backend/src/auth",
        "backend/test",
    ],
    file_templates=[
        FileTemplate("backend/src/main.ts", "config", "应用入口"),
        FileTemplate("backend/src/app.module.ts", "config", "根模块"),
        FileTemplate("backend/src/common/guards/auth.guard.ts", "util", "认证守卫"),
        FileTemplate("backend/src/common/decorators/roles.decorator.ts", "util", "角色装饰器"),
        FileTemplate("backend/src/config/configuration.ts", "config", "配置管理"),
    ],
    dependencies=[
        "@nestjs/common",
        "@nestjs/core",
        "@nestjs/platform-express",
        "@nestjs/config",
        "@nestjs/jwt",
        "@nestjs/passport",
        "@nestjs/typeorm",
        "passport",
        "passport-jwt",
        "typeorm",
        "pg",
        "class-validator",
        "class-transformer",
    ],
    dev_dependencies=[
        "@nestjs/cli",
        "@nestjs/schematics",
        "@nestjs/testing",
        "@types/express",
        "@types/node",
        "@types/passport-jwt",
        "typescript",
        "jest",
    ],
    config_files={
        "package.json": """{
  "name": "backend",
  "version": "1.0.0",
  "scripts": {
    "build": "nest build",
    "start": "nest start",
    "start:dev": "nest start --watch",
    "test": "jest"
  }
}""",
        "tsconfig.json": """{
  "compilerOptions": {
    "module": "commonjs",
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "target": "ES2021",
    "sourceMap": true,
    "outDir": "./dist"
  }
}"""
    }
)

# ==================== 前端项目结构 ====================

REACT_TS_STRUCTURE = ProjectStructure(
    name="React TypeScript",
    tech_stack=TechStack.REACT_TS,
    description="React + TypeScript 前端项目标准结构",
    base_path="frontend",
    directories=[
        "frontend/src",
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/hooks",
        "frontend/src/services",
        "frontend/src/store",
        "frontend/src/types",
        "frontend/src/utils",
        "frontend/src/styles",
        "frontend/src/assets",
        "frontend/public",
    ],
    file_templates=[
        FileTemplate("frontend/src/main.tsx", "config", "应用入口"),
        FileTemplate("frontend/src/App.tsx", "config", "根组件"),
        FileTemplate("frontend/src/index.css", "config", "全局样式"),
        FileTemplate("frontend/src/types/index.ts", "model", "类型定义"),
        FileTemplate("frontend/src/utils/request.ts", "util", "HTTP请求封装"),
        FileTemplate("frontend/src/services/api.ts", "service", "API服务"),
    ],
    dependencies=[
        "react",
        "react-dom",
        "react-router-dom",
        "@tanstack/react-query",
        "axios",
        "zustand",
        "antd",
        "@ant-design/icons",
    ],
    dev_dependencies=[
        "@types/react",
        "@types/react-dom",
        "@vitejs/plugin-react",
        "typescript",
        "vite",
        "eslint",
        "@typescript-eslint/parser",
    ],
    config_files={
        "package.json": """{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}""",
        "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}"""
    }
)

NEXT_JS_STRUCTURE = ProjectStructure(
    name="Next.js",
    tech_stack=TechStack.NEXT_JS,
    description="Next.js 全栈前端项目标准结构",
    base_path="frontend",
    directories=[
        "frontend/src/app",
        "frontend/src/components",
        "frontend/src/lib",
        "frontend/src/hooks",
        "frontend/src/types",
        "frontend/src/styles",
        "frontend/public",
    ],
    file_templates=[
        FileTemplate("frontend/src/app/layout.tsx", "config", "根布局"),
        FileTemplate("frontend/src/app/page.tsx", "page", "首页"),
        FileTemplate("frontend/src/lib/api.ts", "service", "API服务"),
        FileTemplate("frontend/src/types/index.ts", "model", "类型定义"),
    ],
    dependencies=[
        "next",
        "react",
        "react-dom",
        "@tanstack/react-query",
        "axios",
        "zustand",
    ],
    dev_dependencies=[
        "@types/node",
        "@types/react",
        "@types/react-dom",
        "typescript",
        "eslint",
        "eslint-config-next",
    ],
    config_files={
        "package.json": """{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }
}"""
    }
)

VUE_TS_STRUCTURE = ProjectStructure(
    name="Vue TypeScript",
    tech_stack=TechStack.VUE_TS,
    description="Vue 3 + TypeScript 前端项目标准结构",
    base_path="frontend",
    directories=[
        "frontend/src",
        "frontend/src/views",
        "frontend/src/components",
        "frontend/src/router",
        "frontend/src/store",
        "frontend/src/api",
        "frontend/src/types",
        "frontend/src/utils",
        "frontend/src/assets",
        "frontend/src/styles",
    ],
    file_templates=[
        FileTemplate("frontend/src/main.ts", "config", "应用入口"),
        FileTemplate("frontend/src/App.vue", "config", "根组件"),
        FileTemplate("frontend/src/types/index.ts", "model", "类型定义"),
        FileTemplate("frontend/src/utils/request.ts", "util", "HTTP请求封装"),
        FileTemplate("frontend/src/api/index.ts", "service", "API服务"),
    ],
    dependencies=[
        "vue",
        "vue-router",
        "pinia",
        "axios",
        "element-plus",
        "@element-plus/icons-vue",
    ],
    dev_dependencies=[
        "@vitejs/plugin-vue",
        "typescript",
        "vite",
        "vue-tsc",
        "@types/node",
    ],
    config_files={
        "package.json": """{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  }
}"""
    }
)


# ==================== 项目结构注册表 ====================

PROJECT_STRUCTURES: dict[TechStack, ProjectStructure] = {
    # 后端
    TechStack.PYTHON_FASTAPI: FASTAPI_STRUCTURE,
    TechStack.NODE_NESTJS: NESTJS_STRUCTURE,

    # 前端
    TechStack.REACT_TS: REACT_TS_STRUCTURE,
    TechStack.NEXT_JS: NEXT_JS_STRUCTURE,
    TechStack.VUE_TS: VUE_TS_STRUCTURE,
}


def get_project_structure(tech_stack: TechStack) -> ProjectStructure | None:
    """获取指定技术栈的项目结构"""
    return PROJECT_STRUCTURES.get(tech_stack)


def list_available_stacks() -> list[TechStack]:
    """列出所有可用的技术栈"""
    return list(PROJECT_STRUCTURES.keys())


def get_backend_stacks() -> list[TechStack]:
    """获取所有后端技术栈"""
    return [
        TechStack.PYTHON_FASTAPI,
        TechStack.PYTHON_FLASK,
        TechStack.NODE_EXPRESS,
        TechStack.NODE_NESTJS,
        TechStack.GO_GIN,
        TechStack.JAVA_SPRING,
    ]


def get_frontend_stacks() -> list[TechStack]:
    """获取所有前端技术栈"""
    return [
        TechStack.REACT_TS,
        TechStack.REACT_JS,
        TechStack.VUE_TS,
        TechStack.VUE_JS,
        TechStack.NEXT_JS,
        TechStack.NUXT_TS,
    ]


__all__ = [
    "TechStack",
    "FileTemplate",
    "ProjectStructure",
    "get_project_structure",
    "list_available_stacks",
    "get_backend_stacks",
    "get_frontend_stacks",
    # 项目结构
    "FASTAPI_STRUCTURE",
    "NESTJS_STRUCTURE",
    "REACT_TS_STRUCTURE",
    "NEXT_JS_STRUCTURE",
    "VUE_TS_STRUCTURE",
]
