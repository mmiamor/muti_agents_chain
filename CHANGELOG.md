# 更新日志

所有重要的项目变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 计划中
- 监控 Dashboard

### 新增 ✨

#### 自定义工作流链路配置
- **灵活执行模式**: 支持顺序、并行、条件执行
- **Agent 跳过**: 可跳过不需要的 Agent
- **自定义审查策略**: 自动、人工、跳过、条件审查
- **并行执行**: 多个 Agent 同时执行提高效率
- **条件分支**: 基于规则的条件执行
- **工作流模板**: 预定义的常用工作流模板
- **YAML/JSON 配置**: 文件化的配置管理

#### 工作流配置模型
- `src/models/workflow.py` - 完整的工作流配置模型
- **AgentNodeConfig** - Agent 节点配置
- **WorkflowStage** - 工作流阶段配置
- **WorkflowConfig** - 完整工作流配置
- **WorkflowTemplates** - 预定义模板集合

#### 工作流引擎
- `src/core/workflow_engine.py` - 工作流执行引擎
- **顺序执行器** - 按顺序执行 Agent
- **并行执行器** - 并行执行多个 Agent
- **条件执行器** - 基于条件执行分支
- **审查集成** - 自动审查和修复

#### 工作流加载器
- `src/core/workflow_loader.py` - 配置加载器
- **模板加载** - 加载预定义模板
- **文件加载** - 从 YAML/JSON 加载
- **自定义创建** - 编程方式创建工作流

#### 预定义工作流
- **full_pipeline** - 完整开发流水线
- **rapid_prototype** - 快速原型（无审查）
- **design_only** - 仅设计阶段
- **backend_only** - 仅后端开发
- **frontend_only** - 仅前端开发

#### 配置文件
- `workflows/full_pipeline.yaml` - 完整流水线配置
- `workflows/rapid_prototype.yaml` - 快速原型配置
- `workflows/backend_only.yaml` - 后端工作流
- `workflows/frontend_only.yaml` - 前端工作流

#### 文档和示例
- `docs/CUSTOM_WORKFLOW.md` - 完整配置指南
- `examples/custom_workflow_example.py` - 使用示例

#### Agent 专用模型配置
- **独立模型配置**: 每个 Agent 可配置不同的 LLM 模型
- **环境变量支持**: 通过 `.env.*` 文件配置 Agent 专用模型
- **默认模型回退**: 未配置的 Agent 自动使用默认模型
- **运行时查询**: 支持查询当前 Agent 模型配置
- **灵活配置**: 可根据成本、性能需求为不同 Agent 选择最合适的模型

#### 配置模块
- `src/config/agent_models.py` - Agent 模型配置管理
- `AgentModelConfig` - 模型配置类
- `parse_agent_model_config()` - 配置解析函数

#### 工厂增强
- `src/agents/factory.py` - 支持创建 Agent 专用 LLM 实例
- `create_llm(agent_name)` - 为指定 Agent 创建 LLM

#### 配置文件
- `.env.agent_models_example` - Agent 模型配置示例
- `.env.example` - 更新：添加 Agent 模型配置说明

#### 测试和文档
- `test_agent_models.py` - Agent 模型配置测试套件
- `docs/AGENT_MODEL_CONFIG.md` - 完整的配置指南

### 优化 🚀

#### Agent 节点更新
- PM Agent 现在使用配置的专用模型
- 所有 Agent 节点支持模型参数注入

---

## [0.1.0] - 2026-03-30
/
### 新增 ✨

#### 多环境配置系统
- **三环境支持**: Development、Testing、Production
- **智能环境检测**: 环境变量 → Git 分支 → 默认开发环境
- **环境特定配置**: 每个环境独立的配置文件
- **动态环境切换**: 支持运行时环境切换
- **便捷函数**: `is_development()`, `is_testing()`, `is_production()`
- **配置验证**: 完整的配置完整性检查

#### 环境配置文件
- `.env.development` - 开发环境配置
- `.env.testing` - 测试环境配置
- `.env.production` - 生产环境配置

#### 配置模块
- `src/config/environment.py` - 环境管理核心
- `src/config/development.py` - 开发环境配置类
- `src/config/testing.py` - 测试环境配置类
- `src/config/production.py` - 生产环境配置类
- `src/config/settings.py` - 重构的配置入口

#### 测试工具
- `test_environment.py` - 综合环境配置测试
- `test_env_switching.py` - 环境切换演示

#### 文档
- `docs/ENVIRONMENT_QUICK_START.md` - 环境配置快速指南
- `docs/MULTI_ENVIRONMENT_CONFIG.md` - 多环境配置详解
- `docs/MULTI_ENVIRONMENT_COMPLETE.md` - 多环境实现报告
- `PROJECT_STATUS.md` - 项目状态总览
- `CHANGELOG.md` - 本更新日志

### 优化 🚀

#### README 优化
- 重新组织项目介绍
- 添加多环境配置说明
- 更新技术栈表格
- 完善使用示例
- 添加环境对比表格
- 更新项目结构图

#### .gitignore 优化
- 排除所有 `.env.*` 文件
- 保留 `.env.example` 作为模板

### 修复 🐛

- 修复数据库模型导入语法错误（trailing comma）
- 修复环境检测逻辑（main 分支不再自动识别为生产环境）

### 测试 ✅

- 所有环境配置测试通过（5/5）
- 环境切换测试验证
- 配置完整性检查通过

---

## [0.0.6] - 2026-03-29

### 新增 ✨

#### 持久化系统
- **数据库模型**: Thread, Artifact, Review, Message, HumanIntervention, PerformanceMetrics
- **持久化服务**: 完整的 CRUD 操作
- **人工干预服务**: 任务创建、查询、解决
- **持久化装饰器**: `@with_persistence` 自动保存 Agent 结果

#### API 接口
- **人工干预 API**: `/api/v1/human/tasks/*`
- **数据查询 API**: `/api/v1/data/*`

#### 增强流式输出
- **细粒度事件**: thinking 事件类型
- **持久化集成**: 自动保存到数据库
- **错误恢复**: 优雅的异常处理

### 文档 📚

- `docs/PERSISTENCE_COMPLETE.md` - 持久化系统完成报告

---

## [0.0.5] - 2026-03-28

### 新增 ✨

#### 智能上下文管理
- **自动压缩**: 当消息超过阈值时自动压缩
- **智能保留**: 保留关键信息（系统提示、用户需求、决策点）
- **Token 优化**: 平均节省 30-60% 的 token 使用量
- **滑动窗口**: 保留最近的消息维持对话连贯性

#### 流式输出系统
- **SSE 支持**: Server-Sent Events 实时推送
- **7 种事件类型**: phase, progress, artifact, thinking, review, error, done
- **实时进度更新**: 每个阶段都有进度百分比
- **优雅错误处理**: 详细的错误信息推送

### 文档 📚

- `docs/CONTEXT_MANAGEMENT.md` - 上下文管理指南

---

## [0.0.4] - 2026-03-27

### 新增 ✨

#### Multi-Agent 系统
- **7 个专业 Agent**: PM, Architect, Design, Backend Dev, Frontend Dev, QA, Reviewer
- **自动审查机制**: 每个产出物经过自动审查
- **反馈循环**: 不合格自动修改（最多 3 次）
- **人工干预**: 超过修改限制时触发人工干预

#### 强类型数据模型
- **PRD 模型**: 产品需求文档
- **TRD 模型**: 技术设计文档
- **DesignDocument 模型**: UI/UX 设计文档
- **BackendCodeSpec 模型**: 后端代码规范
- **FrontendCodeSpec 模型**: 前端代码规范
- **QAReport 模型**: 质量报告

### 优化 🚀

- **LangGraph 编排**: 基于状态机的流程控制
- **自动路由**: 智能判断下一步操作
- **检查点支持**: 支持流程回滚

---

## [0.0.3] - 2026-03-26

### 新增 ✨

#### 项目初始化
- **基础结构**: 完整的项目目录结构
- **配置系统**: 环境变量管理
- **日志系统**: 结构化日志输出

#### LLM 服务
- **智谱 GLM 集成**: 支持智谱 AI 的 GLM 系列
- **限流处理**: 自动重试和延迟控制
- **错误处理**: 优雅的异常处理

---

## [0.0.2] - 2026-03-25

### 新增 ✨

#### FastAPI 服务
- **REST API**: 基础的 HTTP 服务
- **Swagger 文档**: 自动生成的 API 文档
- **健康检查**: `/health` 端点

---

## [0.0.1] - 2026-03-24

### 新增 ✨

#### 项目启动
- **项目创建**: 初始化项目结构
- **依赖管理**: requirements.txt
- **基础文档**: README.md

---

## 版本说明

### 版本格式

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 更新类型

- **新增**: 新功能
- **优化**: 现有功能的改进
- **修复**: Bug 修复
- **安全**: 安全相关的修复
- **弃用**: 即将移除的功能
- **移除**: 已移除的功能
- **文档**: 文档更新

---

**当前版本**: v0.1.0
**最后更新**: 2026-03-30
