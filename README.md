# AI Backend - LLMChain
> 自动化 AI 后台服务框架

## 环境要求

- Python 3.13 (通过 pyenv 管理)
- pyenv-win 3.1.1+

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
python -m src.main
```

## 项目结构

```
llmchain/
├── src/
│   ├── main.py              # 应用入口
│   ├── core/                # 核心引擎
│   │   ├── __init__.py
│   │   ├── engine.py        # 主引擎
│   │   ├── scheduler.py     # 任务调度器
│   │   └── pipeline.py      # 处理管道
│   ├── api/                 # API 层
│   │   ├── __init__.py
│   │   ├── server.py        # HTTP 服务
│   │   └── routes.py        # 路由定义
│   ├── services/            # 业务服务
│   │   ├── __init__.py
│   │   ├── llm_service.py   # LLM 调用服务
│   │   ├── chain_service.py # Chain 编排服务
│   │   └── memory_service.py# 记忆管理服务
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic 模型
│   ├── utils/               # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py        # 日志配置
│   │   └── helpers.py       # 通用工具
│   └── config/              # 配置管理
│       ├── __init__.py
│       └── settings.py      # 环境配置
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/                 # 运维脚本
├── logs/                    # 日志目录
├── data/                    # 数据目录
├── .python-version          # pyenv 版本锁定
├── requirements.txt
└── .env.example
```

## 技术栈

- **FastAPI** — 高性能 Web 框架
- **Pydantic** — 数据验证
- **LangChain** — LLM 编排
- **Redis** — 缓存 / 队列
- **SQLAlchemy** — ORM
