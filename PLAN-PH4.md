# Phase 3 优化 + Phase 4 Design Agent 实施计划

## 一、Phase 3 优化（重构）

### 1.1 统一 LLM 工厂
- 新建 `src/agents/factory.py`，提取 `create_llm()` 公共方法
- PM / Reviewer / Architect 节点统一调用，消除重复代码

### 1.2 统一 revision 计数
- `revision_count` + `architect_revision_count` → `revision_counts: dict[str, int]`
- Key 为 agent name（如 `"pm_agent"`, `"architect_agent"`）
- router / reviewer_node 统一读取

### 1.3 Router 可扩展化
- 用「阶段→Agent 映射」替代 if-else 链
- `STAGE_REGISTRY` 定义每个阶段的 agent、产出物字段、下一阶段
- router 根据 stage 自动查找，新增 Agent 只需注册一行

## 二、Phase 4 Design Agent

### 2.1 数据模型 — DesignDocument
```
DesignDocument:
  - page_specs: list[PageSpec]     # 页面/组件规格
  - user_journey: str               # 用户旅程 Mermaid flowchart
  - design_tokens: DesignTokens     # 设计 Token（配色、字体、间距）
  - responsive_strategy: str        # 响应式策略
  - component_library: list[str]    # UI 组件清单
```

### 2.2 Design Agent
- 输入：PRD + TRD
- 输出：DesignDocument（JSON）
- 审查反馈处理（同 PM/Architect）

### 2.3 编排更新
- PM → Reviewer → Architect → Reviewer → **Design** → Reviewer → END

### 2.4 测试
- unit: DesignDocument 模型、design_node、router Design 阶段
- integration: PM→Architect→Design 全流程
- E2E: 真实 LLM 全链路
