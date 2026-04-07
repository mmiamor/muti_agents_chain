# 代码生成系统使用文档

## 概述

本系统实现了精确的前后端代码定位与生成功能，确保生成的代码文件位置准确、职责清晰。系统采用模块化设计，支持多种技术栈。

## 核心功能

### 1. 精确的文件路径定位

- **自动化路径解析**：根据文件角色自动确定文件路径
- **冲突检测**：自动检测文件路径冲突
- **依赖验证**：验证文件之间的依赖关系
- **增量更新**：支持增量更新已有文件

### 2. 多技术栈支持

#### 后端技术栈
- Python FastAPI（默认）
- Python Flask
- Node.js Express
- Node.js NestJS
- Go Gin
- Java Spring Boot

#### 前端技术栈
- React + TypeScript（默认）
- React + JavaScript
- Vue 3 + TypeScript
- Vue 3 + JavaScript
- Next.js
- Nuxt.js

### 3. 职责分离

#### 后端文件角色
| 角色 | 说明 | 路径模板 |
|------|------|----------|
| `model` | 数据模型 | `app/models/{module}.py` |
| `controller` | API 控制器 | `app/api/v1/endpoints/{module}.py` |
| `service` | 业务逻辑 | `app/services/{module}_service.py` |
| `route` | 路由配置 | `app/api/v1/api.py` |
| `middleware` | 中间件 | `app/middlewares/{module}.py` |
| `config` | 配置文件 | `app/core/{module}.py` |
| `util` | 工具函数 | `app/utils/{module}.py` |

#### 前端文件角色
| 角色 | 说明 | 路径模板 |
|------|------|----------|
| `page` | 页面组件 | `src/pages/{module}.tsx` |
| `component` | 通用组件 | `src/components/{module}.tsx` |
| `hook` | 自定义 Hook | `src/hooks/{module}.ts` |
| `store` | 状态管理 | `src/store/{module}.ts` |
| `api` | API 服务 | `src/services/{module}.ts` |
| `type` | 类型定义 | `src/types/{module}.ts` |
| `style` | 样式文件 | `src/styles/{module}.css` |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      代码生成系统                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ 后端代码生成器    │      │ 前端代码生成器    │            │
│  │ (BackendCodeGen) │      │ (FrontendCodeGen)│            │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                          │                      │
│           └──────────┬───────────────┘                      │
│                      │                                       │
│           ┌──────────▼──────────┐                          │
│           │  代码文件定位系统     │                          │
│           │ (CodePathResolver)  │                          │
│           └──────────┬──────────┘                          │
│                      │                                       │
│           ┌──────────▼──────────┐                          │
│           │  项目结构配置        │                          │
│           │ (ProjectStructure)  │                          │
│           └─────────────────────┘                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 使用方式

### 1. 在 Agent 节点中使用

```python
from src.services.backend_codegen_service import BackendCodeGenerator
from src.services.frontend_codegen_service import FrontendCodeGenerator
from src.services.code_locator_service import CodeFileOrganizer

# 后端代码生成
backend_generator = BackendCodeGenerator()
file_organizer = CodeFileOrganizer(project_type="backend")

# 生成代码结构
locations = file_organizer.organize_backend_code(trd)

# 生成代码
code_spec = backend_generator.generate_from_trd(trd, output_dir="./output")

# 前端代码生成
frontend_generator = FrontendCodeGenerator()
file_organizer = CodeFileOrganizer(project_type="frontend")

# 生成代码结构
locations = file_organizer.organize_frontend_code(design)

# 生成代码
code_spec = frontend_generator.generate_from_design(design, trd, output_dir="./output")
```

### 2. 自定义项目结构

```python
from src.services.codegen_service import ProjectStructure, TechStack, FileTemplate

# 定义自定义项目结构
custom_structure = ProjectStructure(
    name="Custom Backend",
    tech_stack=TechStack.PYTHON_FASTAPI,
    description="自定义后端项目结构",
    base_path="backend",
    directories=[
        "backend/src",
        "backend/src/api",
        "backend/src/core",
        # ... 更多目录
    ],
    file_templates=[
        FileTemplate(
            path="backend/src/main.py",
            content_type="config",
            description="应用入口",
            required=True,
        ),
        # ... 更多文件模板
    ],
    dependencies=[
        "fastapi>=0.104.0",
        # ... 更多依赖
    ],
)

# 使用自定义结构
generator = BackendCodeGenerator(project_structure=custom_structure)
```

### 3. 路径冲突检测

```python
from src.services.code_locator_service import CodePathResolver

resolver = CodePathResolver(project_type="backend")

# 解析多个文件位置
locations = [
    resolver.resolve("user", FileRole.MODEL),
    resolver.resolve("user", FileRole.SERVICE),
    # ... 更多文件
]

# 检测冲突
conflicts = resolver.detect_conflicts(locations)
if conflicts:
    for path, files in conflicts.items():
        print(f"冲突: {path} 被 {len(files)} 个文件使用")
        for file in files:
            print(f"  - {file.module} ({file.role})")
```

## 生成代码示例

### 后端代码（FastAPI）

生成的项目结构：
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   └── security.py      # 安全工具
│   ├── db/
│   │   ├── session.py       # 数据库会话
│   │   └── base.py          # 数据库基类
│   ├── models/
│   │   └── __init__.py      # 数据模型
│   ├── schemas/
│   │   └── __init__.py      # Pydantic 模型
│   ├── api/
│   │   └── v1/
│   │       ├── api.py       # 路由聚合
│   │       └── endpoints/
│   │           ├── users.py # 用户 API
│   │           └── items.py # 项目 API
│   └── services/
│       └── item_service.py  # 业务逻辑
├── requirements.txt
├── .env.example
└── Dockerfile
```

### 前端代码（React + TypeScript）

生成的项目结构：
```
frontend/
├── src/
│   ├── main.tsx             # 应用入口
│   ├── App.tsx              # 根组件
│   ├── index.css            # 全局样式
│   ├── pages/
│   │   ├── Home.tsx         # 首页
│   │   └── User.tsx         # 用户页
│   ├── components/
│   │   └── Layout/
│   │       ├── Header.tsx   # 顶部导航
│   │       ├── Sidebar.tsx  # 侧边栏
│   │       └── Footer.tsx   # 页脚
│   ├── services/
│   │   └── api.ts           # API 服务
│   ├── types/
│   │   └── index.ts         # 类型定义
│   ├── utils/
│   │   └── request.ts       # HTTP 封装
│   └── styles/
│       └── theme.css        # 主题样式
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 配置选项

### 环境变量

```bash
# 代码生成配置
CODEGEN_OUTPUT_DIR=./output
CODEGEN_OVERWRITE_EXISTING=false
CODEGEN_ENABLE_CONFLICT_CHECK=true

# 技术栈配置
DEFAULT_BACKEND_STACK=python_fastapi
DEFAULT_FRONTEND_STACK=react_ts
```

## 最佳实践

### 1. 模块命名规范

- 使用小写字母和下划线：`user_profile`, `item_service`
- 避免使用连字符和空格
- 保持名称简洁但描述性强

### 2. 文件组织原则

- **单一职责**：每个文件只负责一个功能模块
- **清晰分层**：严格按照 MVC 或类似架构组织代码
- **依赖注入**：使用依赖注入管理模块间依赖

### 3. 代码生成流程

1. **分析需求**：理解 TRD/设计文档
2. **规划结构**：使用文件组织器规划代码结构
3. **检测冲突**：检查路径冲突和依赖问题
4. **生成代码**：使用代码生成器生成文件
5. **验证结果**：检查生成代码的完整性和正确性

## 故障处理

### 常见问题

1. **路径冲突**
   - 症状：多个文件映射到同一路径
   - 解决：检查模块命名，使用更具体的名称

2. **依赖缺失**
   - 症状：生成的代码引用了不存在的文件
   - 解决：使用依赖验证功能，确保所有依赖文件都已生成

3. **权限错误**
   - 症状：无法写入输出目录
   - 解决：检查输出目录权限，确保有写入权限

## 扩展指南

### 添加新的技术栈

1. 在 `codegen_service.py` 中定义新的项目结构
2. 实现对应的代码生成器
3. 添加路径映射规则
4. 注册到技术栈枚举中

### 自定义代码模板

1. 创建自定义模板文件
2. 在代码生成器中引用模板
3. 使用模板变量动态生成内容

## 总结

本代码生成系统通过以下方式确保代码生成的准确性和可靠性：

- ✅ 精确的文件路径定位
- ✅ 清晰的职责分离
- ✅ 完善的冲突检测
- ✅ 灵活的技术栈支持
- ✅ 可扩展的架构设计

系统已集成到后端和前端开发 Agent 中，可以自动生成符合最佳实践的代码结构。
