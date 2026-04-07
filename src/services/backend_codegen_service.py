"""
后端代码生成服务 - 精确的文件路径定位和代码生成

基于项目结构配置，为后端生成准确位置、职责清晰的代码文件
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.models.document_models import TRD, BackendCodeSpec, CodeFile
from src.services.codegen_service import (
    ProjectStructure,
    get_project_structure,
    TechStack,
)

logger = logging.getLogger("backend_codegen")


class BackendCodeGenerator:
    """后端代码生成器"""

    def __init__(self, project_structure: ProjectStructure | None = None):
        """
        初始化后端代码生成器

        Args:
            project_structure: 项目结构定义，默认使用 FastAPI
        """
        self.project_structure = project_structure or get_project_structure(TechStack.PYTHON_FASTAPI)
        if not self.project_structure:
            raise ValueError("Project structure not found")

    def generate_from_trd(self, trd: TRD, output_dir: str = "./output") -> BackendCodeSpec:
        """
        根据 TRD 生成后端代码

        Args:
            trd: 技术设计文档
            output_dir: 输出目录

        Returns:
            BackendCodeSpec: 生成的后端代码规格
        """
        logger.info(f"Generating backend code with stack: {self.project_structure.tech_stack}")

        base_path = Path(output_dir) / self.project_structure.base_path

        # 生成项目结构
        project_structure = self._generate_project_structure(base_path)

        # 生成核心文件
        core_files = self._generate_core_files(trd, base_path)

        # 生成数据模型
        model_files = self._generate_models(trd, base_path)

        # 生成 API 端点
        controller_files = self._generate_controllers(trd, base_path)

        # 生成业务逻辑层
        service_files = self._generate_services(trd, base_path)

        # 生成配置文件
        config_files = self._generate_configs(trd, base_path)

        # 合并所有文件
        all_files = [project_structure, *core_files, *model_files, *controller_files, *service_files, *config_files]

        # 生成依赖信息
        dependencies = self._generate_dependencies()

        return BackendCodeSpec(
            project_structure=project_structure,
            files=all_files,
            setup_commands=self._generate_setup_commands(base_path),
            dependencies=dependencies,
        )

    def _generate_project_structure(self, base_path: Path) -> CodeFile:
        """生成项目结构文件"""
        structure_str = self._build_directory_tree(base_path)

        return CodeFile(
            path=str(base_path / "STRUCTURE.md"),
            description="项目目录结构说明",
            content=structure_str,
        )

    def _build_directory_tree(self, base_path: Path) -> str:
        """构建目录树"""
        lines = [f"# {self.project_structure.name} 项目结构\n"]
        lines.append("```\n")

        for directory in self.project_structure.directories:
            rel_path = Path(directory).relative_to(self.project_structure.base_path)
            lines.append(f"{self.project_structure.base_path}/{rel_path}/")

        lines.append("```\n")
        lines.append("\n## 目录说明\n")

        for template in self.project_structure.file_templates:
            rel_path = Path(template.path).relative_to(self.project_structure.base_path)
            lines.append(f"- **{rel_path}**: {template.description}")

        return "\n".join(lines)

    def _generate_core_files(self, trd: TRD, base_path: Path) -> list[CodeFile]:
        """生成核心文件"""
        files = []

        # main.py - 应用入口
        main_content = self._generate_main_file(trd)
        files.append(CodeFile(
            path=str(base_path / "app" / "main.py"),
            description="FastAPI 应用入口",
            content=main_content,
        ))

        # config.py - 配置管理
        config_content = self._generate_config_file(trd)
        files.append(CodeFile(
            path=str(base_path / "app" / "core" / "config.py"),
            description="配置管理",
            content=config_content,
        ))

        # security.py - 安全相关
        security_content = self._generate_security_file(trd)
        files.append(CodeFile(
            path=str(base_path / "app" / "core" / "security.py"),
            description="安全工具（JWT、密码哈希）",
            content=security_content,
        ))

        # database session
        db_content = self._generate_db_session_file(trd)
        files.append(CodeFile(
            path=str(base_path / "app" / "db" / "session.py"),
            description="数据库会话管理",
            content=db_content,
        ))

        return files

    def _generate_main_file(self, trd: TRD) -> str:
        """生成 main.py"""
        return '''"""
FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
'''

    def _generate_config_file(self, trd: TRD) -> str:
        """生成 config.py"""
        return '''"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""

    # 项目信息
    PROJECT_NAME: str = "FastAPI Project"
    PROJECT_DESCRIPTION: str = "FastAPI Backend Application"
    VERSION: str = "1.0.0"

    # API 配置
    API_V1_STR: str = "/api/v1"

    # CORS 配置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./app.db"

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
'''

    def _generate_security_file(self, trd: TRD) -> str:
        """生成 security.py"""
        return '''"""
安全相关工具 - JWT 和密码哈希
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
'''

    def _generate_db_session_file(self, trd: TRD) -> str:
        """生成数据库会话文件"""
        return '''"""
数据库会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

    def _generate_models(self, trd: TRD, base_path: Path) -> list[CodeFile]:
        """生成数据模型"""
        files = []

        # 根据 ER 图生成模型
        base_model_content = self._generate_base_model(trd)
        files.append(CodeFile(
            path=str(base_path / "app" / "models" / "__init__.py"),
            description="数据模型定义",
            content=base_model_content,
        ))

        return files

    def _generate_base_model(self, trd: TRD) -> str:
        """根据 ER 图生成基础模型"""
        # 解析 ER 图中的表结构
        return '''"""
SQLAlchemy 数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class BaseModel(Base):
    """基础模型类"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # 关系
    # items = relationship("Item", back_populates="owner")


class Item(BaseModel):
    """项目模型示例"""
    __tablename__ = "items"

    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # 关系
    # owner = relationship("User", back_populates="items")
'''

    def _generate_controllers(self, trd: TRD, base_path: Path) -> list[CodeFile]:
        """生成 API 端点"""
        files = []

        # API 路由入口
        api_content = self._generate_api_router(trd)
        files.append(CodeFile(
            path=str(base_path / "app" / "api" / "v1" / "api.py"),
            description="API 路由聚合",
            content=api_content,
        ))

        # 根据 API 端点定义生成具体的路由文件
        for endpoint in trd.api_endpoints:
            endpoint_content = self._generate_endpoint_file(endpoint, trd)
            files.append(CodeFile(
                path=str(base_path / "app" / "api" / "v1" / "endpoints" / f"{endpoint.path.strip('/').replace('/', '_')}.py"),
                description=f"API 端点: {endpoint.method} {endpoint.path}",
                content=endpoint_content,
            ))

        return files

    def _generate_api_router(self, trd: TRD) -> str:
        """生成 API 路由聚合文件"""
        return '''"""
API 路由聚合
"""
from fastapi import APIRouter

from app.api.v1.endpoints import items, users

api_router = APIRouter()

# 注册各个端点路由
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
'''

    def _generate_endpoint_file(self, endpoint: Any, trd: TRD) -> str:
        """生成单个端点文件"""
        return f'''"""
{endpoint.description} API 端点
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.item import Item, ItemCreate, ItemUpdate

router = APIRouter()


@router.{endpoint.method.lower()}("{endpoint.path}", response_model=Item)
async def {endpoint.path.strip('/').replace('/', '_')}_{endpoint.method.lower()}(
    *,
    db: Session = Depends(get_db),
    # item_in: ItemCreate,
):
    """
    {endpoint.description}
    """
    # 实现端点逻辑
    return {{"message": "{endpoint.description}"}}


'''

    def _generate_services(self, trd: TRD, base_path: Path) -> list[CodeFile]:
        """生成业务逻辑层"""
        files = []

        service_content = self._generate_service_template(trd)
        files.append(CodeFile(
            path=str(base_path / "app" / "services" / "item_service.py"),
            description="业务逻辑服务",
            content=service_content,
        ))

        return files

    def _generate_service_template(self, trd: TRD) -> str:
        """生成服务模板"""
        return '''"""
业务逻辑服务层
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    """项目业务逻辑"""

    @staticmethod
    def get(db: Session, item_id: int) -> Optional[Item]:
        """获取单个项目"""
        return db.query(Item).filter(Item.id == item_id).first()

    @staticmethod
    def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[Item]:
        """获取项目列表"""
        return db.query(Item).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, obj_in: ItemCreate) -> Item:
        """创建项目"""
        db_obj = Item(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(db: Session, db_obj: Item, obj_in: ItemUpdate) -> Item:
        """更新项目"""
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, item_id: int) -> Item:
        """删除项目"""
        obj = db.query(Item).get(item_id)
        db.delete(obj)
        db.commit()
        return obj


item_service = ItemService()
'''

    def _generate_configs(self, trd: TRD, base_path: Path) -> list[CodeFile]:
        """生成配置文件"""
        files = []

        # requirements.txt
        requirements = "\n".join(self.project_structure.dependencies)
        files.append(CodeFile(
            path=str(base_path / "requirements.txt"),
            description="Python 依赖",
            content=requirements,
        ))

        # .env.example
        env_content = "\n".join([
            f"{k}=" for k in ["OPENAI_API_KEY", "DATABASE_URL", "SECRET_KEY"]
        ])
        files.append(CodeFile(
            path=str(base_path / ".env.example"),
            description="环境变量示例",
            content=env_content,
        ))

        # Dockerfile
        docker_content = self._generate_dockerfile(trd)
        files.append(CodeFile(
            path=str(base_path / "Dockerfile"),
            description="Docker 配置",
            content=docker_content,
        ))

        return files

    def _generate_dockerfile(self, trd: TRD) -> str:
        """生成 Dockerfile"""
        return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    def _generate_dependencies(self) -> str:
        """生成依赖说明"""
        deps = self.project_structure.dependencies
        dev_deps = self.project_structure.dev_dependencies

        parts = [
            "# 核心依赖\n",
            "\n".join(deps),
            "\n\n# 开发依赖\n",
            "\n".join(dev_deps),
        ]

        return "\n".join(parts)

    def _generate_setup_commands(self, base_path: Path) -> list[str]:
        """生成项目启动命令"""
        return [
            f"cd {base_path}",
            "python -m venv venv",
            "source venv/bin/activate  # Windows: venv\\Scripts\\activate",
            "pip install -r requirements.txt",
            "cp .env.example .env",
            "# 编辑 .env 文件配置环境变量",
            "uvicorn app.main:app --reload",
        ]


__all__ = ["BackendCodeGenerator"]
