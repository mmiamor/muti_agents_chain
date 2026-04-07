"""
前端代码生成服务 - 精确的文件路径定位和代码生成

基于项目结构配置，为前端生成准确位置、职责清晰的代码文件
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.models.document_models import DesignDocument, FrontendCodeSpec, CodeFile
from src.services.codegen_service import (
    ProjectStructure,
    get_project_structure,
    TechStack,
)

logger = logging.getLogger("frontend_codegen")


class FrontendCodeGenerator:
    """前端代码生成器"""

    def __init__(self, project_structure: ProjectStructure | None = None):
        """
        初始化前端代码生成器

        Args:
            project_structure: 项目结构定义，默认使用 React + TypeScript
        """
        self.project_structure = project_structure or get_project_structure(TechStack.REACT_TS)
        if not self.project_structure:
            raise ValueError("Project structure not found")

    def generate_from_design(self, design: DesignDocument, trd: Any, output_dir: str = "./output") -> FrontendCodeSpec:
        """
        根据设计文档生成前端代码

        Args:
            design: UI/UX 设计文档
            trd: 技术设计文档（用于 API 接口信息）
            output_dir: 输出目录

        Returns:
            FrontendCodeSpec: 生成的前端代码规格
        """
        logger.info(f"Generating frontend code with stack: {self.project_structure.tech_stack}")

        base_path = Path(output_dir) / self.project_structure.base_path

        # 生成项目结构
        project_structure = self._generate_project_structure(base_path)

        # 生成核心配置文件
        core_files = self._generate_core_files(design, base_path)

        # 生成页面组件
        page_files = self._generate_pages(design, base_path)

        # 生成通用组件
        component_files = self._generate_components(design, base_path)

        # 生成服务层（API 调用）
        service_files = self._generate_services(design, trd, base_path)

        # 生成类型定义
        type_files = self._generate_types(design, trd, base_path)

        # 生成工具函数
        util_files = self._generate_utils(design, base_path)

        # 生成样式文件
        style_files = self._generate_styles(design, base_path)

        # 合并所有文件
        all_files = [
            project_structure,
            *core_files,
            *page_files,
            *component_files,
            *service_files,
            *type_files,
            *util_files,
            *style_files,
        ]

        # 生成依赖信息
        dependencies = self._generate_dependencies()

        return FrontendCodeSpec(
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

    def _generate_core_files(self, design: DesignDocument, base_path: Path) -> list[CodeFile]:
        """生成核心配置文件"""
        files = []

        # main.tsx - 应用入口
        main_content = self._generate_main_file(design)
        files.append(CodeFile(
            path=str(base_path / "src" / "main.tsx"),
            description="React 应用入口",
            content=main_content,
        ))

        # App.tsx - 根组件
        app_content = self._generate_app_component(design)
        files.append(CodeFile(
            path=str(base_path / "src" / "App.tsx"),
            description="根组件",
            content=app_content,
        ))

        # index.css - 全局样式
        global_styles = self._generate_global_styles(design)
        files.append(CodeFile(
            path=str(base_path / "src" / "index.css"),
            description="全局样式",
            content=global_styles,
        ))

        # vite.config.ts
        vite_config = self._generate_vite_config(design)
        files.append(CodeFile(
            path=str(base_path / "vite.config.ts"),
            description="Vite 配置",
            content=vite_config,
        ))

        # tsconfig.json
        tsconfig = self._generate_tsconfig(design)
        files.append(CodeFile(
            path=str(base_path / "tsconfig.json"),
            description="TypeScript 配置",
            content=tsconfig,
        ))

        return files

    def _generate_main_file(self, design: DesignDocument) -> str:
        """生成 main.tsx"""
        return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider locale={zhCN} theme={{
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 6,
        },
      }}>
        <App />
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
'''

    def _generate_app_component(self, design: DesignDocument) -> str:
        """生成 App.tsx"""
        return '''import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import Header from './components/Layout/Header'
import Sidebar from './components/Layout/Sidebar'
import HomePage from './pages/Home'

const { Content } = Layout

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header />
      <Layout>
        <Sidebar />
        <Content style={{ padding: '24px', background: '#f0f2f5' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            {/* 更多路由... */}
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
'''

    def _generate_global_styles(self, design: DesignDocument) -> str:
        """生成全局样式"""
        tokens = design.design_tokens

        return f''':root {{
  font-family: {tokens.font_family}, system-ui, -apple-system, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  color-scheme: light dark;

  /* 颜色 */
  --color-primary: {tokens.color_primary};
  --color-secondary: {tokens.color_secondary};

  /* 间距 */
  --spacing-unit: {tokens.spacing_unit};

  /* 圆角 */
  --border-radius: {tokens.border_radius};

  /* 字体 */
  --font-sans: {tokens.font_family};
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  min-height: 100vh;
  font-family: var(--font-sans);
}}

#root {{
  max-width: 100%;
}}
'''

    def _generate_vite_config(self, design: DesignDocument) -> str:
        """生成 vite.config.ts"""
        return '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
'''

    def _generate_tsconfig(self, design: DesignDocument) -> str:
        """生成 tsconfig.json"""
        return self.project_structure.config_files.get("tsconfig.json", "")

    def _generate_pages(self, design: DesignDocument, base_path: Path) -> list[CodeFile]:
        """生成页面组件"""
        files = []

        for page_spec in design.page_specs:
            page_content = self._generate_page_component(page_spec, design)
            files.append(CodeFile(
                path=str(base_path / "src" / "pages" / f"{page_spec.page_name}.tsx"),
                description=f"页面: {page_spec.page_name}",
                content=page_content,
            ))

        return files

    def _generate_page_component(self, page_spec: Any, design: DesignDocument) -> str:
        """生成单个页面组件"""
        return f'''import {{ FC }} from 'react'
import {{ Card, Button, Space }} from 'antd'

/**
 * {page_spec.page_name}
 *
 * {page_spec.description}
 */
const {page_spec.page_name.replace(' ', '')}: FC = () => {{
  return (
    <div style={{{{ padding: '24px' }}}}>
      <Card title="{page_spec.page_name}">
        <p>{page_spec.description}</p>

        {/* 页面内容 */}
        <Space>
          <Button type="primary">操作按钮</Button>
          <Button>取消</Button>
        </Space>
      </Card>
    </div>
  )
}}

export default {page_spec.page_name.replace(' ', '')}
'''

    def _generate_components(self, design: DesignDocument, base_path: Path) -> list[CodeFile]:
        """生成通用组件"""
        files = []

        # 布局组件
        layout_components = [
            ("Header", "顶部导航栏"),
            ("Sidebar", "侧边栏"),
            ("Footer", "页脚"),
        ]

        for comp_name, comp_desc in layout_components:
            comp_content = self._generate_layout_component(comp_name, design)
            files.append(CodeFile(
                path=str(base_path / "src" / "components" / "Layout" / f"{comp_name}.tsx"),
                description=f"布局组件: {comp_desc}",
                content=comp_content,
            ))

        return files

    def _generate_layout_component(self, name: str, design: DesignDocument) -> str:
        """生成布局组件"""
        return f'''import {{ FC }} from 'react'
import {{ Layout, Menu, Button }} from 'antd'
import {{ LogoutOutlined }} from '@ant-design/icons'

const {{ Header: AntHeader }} = Layout

/**
 * {name} 组件
 */
const {name}: FC = () => {{
  return (
    <AntHeader style={{{{ background: '#fff', padding: '0 24px' }}}}>
      <div style={{{{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}}}>
        <div style={{{{ fontSize: '18px', fontWeight: 'bold' }}}}>
          Logo
        </div>
        <Button icon={{<LogoutOutlined />}}>退出</Button>
      </div>
    </AntHeader>
  )
}}

export default {name}
'''

    def _generate_services(self, design: DesignDocument, trd: Any, base_path: Path) -> list[CodeFile]:
        """生成 API 服务层"""
        files = []

        # HTTP 请求封装
        request_content = self._generate_request_util(design)
        files.append(CodeFile(
            path=str(base_path / "src" / "utils" / "request.ts"),
            description="HTTP 请求封装",
            content=request_content,
        ))

        # API 服务
        api_content = self._generate_api_service(design, trd)
        files.append(CodeFile(
            path=str(base_path / "src" / "services" / "api.ts"),
            description="API 服务",
            content=api_content,
        ))

        return files

    def _generate_request_util(self, design: DesignDocument) -> str:
        """生成 HTTP 请求工具"""
        return '''import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

// 创建 axios 实例
const instance: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    // 添加 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const { response } = error

    if (response) {
      switch (response.status) {
        case 401:
          message.error('未授权，请重新登录')
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          message.error('拒绝访问')
          break
        case 404:
          message.error('请求地址不存在')
          break
        case 500:
          message.error('服务器错误')
          break
        default:
          message.error(response.data?.message || '请求失败')
      }
    } else {
      message.error('网络连接失败')
    }

    return Promise.reject(error)
  }
)

export default instance
'''

    def _generate_api_service(self, design: DesignDocument, trd: Any) -> str:
        """生成 API 服务"""
        return '''import request from '@/utils/request'

// 用户相关 API
export const userApi = {
  login: (data: { username: string; password: string }) =>
    request.post('/users/login', data),

  getUserInfo: () =>
    request.get('/users/me'),

  updateProfile: (data: any) =>
    request.put('/users/me', data),
}

// 项目相关 API
export const itemApi = {
  getList: (params: any) =>
    request.get('/items', { params }),

  getDetail: (id: number) =>
    request.get(`/items/${id}`),

  create: (data: any) =>
    request.post('/items', data),

  update: (id: number, data: any) =>
    request.put(`/items/${id}`, data),

  delete: (id: number) =>
    request.delete(`/items/${id}`),
}
'''

    def _generate_types(self, design: DesignDocument, trd: Any, base_path: Path) -> list[CodeFile]:
        """生成类型定义"""
        files = []

        type_content = self._generate_global_types(design, trd)
        files.append(CodeFile(
            path=str(base_path / "src" / "types" / "index.ts"),
            description="全局类型定义",
            content=type_content,
        ))

        return files

    def _generate_global_types(self, design: DesignDocument, trd: Any) -> str:
        """生成全局类型"""
        return '''// 通用类型

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PageParams {
  page: number
  pageSize: number
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

// 用户类型

export interface User {
  id: number
  username: string
  email: string
  createdAt: string
}

export interface LoginForm {
  username: string
  password: string
}

// 项目类型

export interface Item {
  id: number
  title: string
  description?: string
  createdAt: string
  updatedAt: string
}

export interface ItemCreate {
  title: string
  description?: string
}

export interface ItemUpdate {
  title?: string
  description?: string
}
'''

    def _generate_utils(self, design: DesignDocument, base_path: Path) -> list[CodeFile]:
        """生成工具函数"""
        files = []

        utils_content = self._generate_common_utils(design)
        files.append(CodeFile(
            path=str(base_path / "src" / "utils" / "index.ts"),
            description="通用工具函数",
            content=utils_content,
        ))

        return files

    def _generate_common_utils(self, design: DesignDocument) -> str:
        """生成通用工具函数"""
        return '''/**
 * 格式化日期
 */
export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleString('zh-CN')
}

/**
 * 防抖
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function (this: any, ...args: Parameters<T>) {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => {
      func.apply(this, args)
    }, wait)
  }
}

/**
 * 节流
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  let previous = 0

  return function (this: any, ...args: Parameters<T>) {
    const now = Date.now()
    const remaining = wait - (now - previous)

    if (remaining <= 0) {
      if (timeout) {
        clearTimeout(timeout)
        timeout = null
      }
      previous = now
      func.apply(this, args)
    } else if (!timeout) {
      timeout = setTimeout(() => {
        previous = Date.now()
        timeout = null
        func.apply(this, args)
      }, remaining)
    }
  }
}
'''

    def _generate_styles(self, design: DesignDocument, base_path: Path) -> list[CodeFile]:
        """生成样式文件"""
        files = []

        # 根据设计 token 生成主题变量
        theme_content = self._generate_theme_styles(design)
        files.append(CodeFile(
            path=str(base_path / "src" / "styles" / "theme.css"),
            description="主题样式变量",
            content=theme_content,
        ))

        return files

    def _generate_theme_styles(self, design: DesignDocument) -> str:
        """生成主题样式"""
        tokens = design.design_tokens

        return f'''/**
 * 主题样式
 */

:root {{
  /* 主色 */
  --color-primary: {tokens.color_primary};
  --color-primary-hover: color-mix(in srgb, {tokens.color_primary} 90%, black);
  --color-primary-active: color-mix(in srgb, {tokens.color_primary} 80%, black);

  /* 辅助色 */
  --color-secondary: {tokens.color_secondary};

  /* 中性色 */
  --color-text-primary: rgba(0, 0, 0, 0.88);
  --color-text-secondary: rgba(0, 0, 0, 0.65);
  --color-text-tertiary: rgba(0, 0, 0, 0.45);

  --color-border: #d9d9d9;
  --color-border-light: #f0f0f0;

  --color-bg-primary: #ffffff;
  --color-bg-secondary: #fafafa;
  --color-bg-tertiary: #f5f5f5;

  /* 圆角 */
  --border-radius: {tokens.border_radius};
  --border-radius-sm: calc({tokens.border_radius} - 2px);
  --border-radius-lg: calc({tokens.border_radius} + 2px);

  /* 间距 */
  --spacing-xs: calc({tokens.spacing_unit} * 1);
  --spacing-sm: calc({tokens.spacing_unit} * 2);
  --spacing-md: calc({tokens.spacing_unit} * 3);
  --spacing-lg: calc({tokens.spacing_unit} * 4);
  --spacing-xl: calc({tokens.spacing_unit} * 5);
}}
'''

    def _generate_dependencies(self) -> str:
        """生成依赖说明"""
        deps = self.project_structure.dependencies
        dev_deps = self.project_structure.dev_dependencies

        parts = [
            "# 生产依赖\n",
            "\n".join(deps),
            "\n\n# 开发依赖\n",
            "\n".join(dev_deps),
        ]

        return "\n".join(parts)

    def _generate_setup_commands(self, base_path: Path) -> list[str]:
        """生成项目启动命令"""
        return [
            f"cd {base_path}",
            "npm install  # 或 pnpm install",
            "npm run dev",
        ]


__all__ = ["FrontendCodeGenerator"]
