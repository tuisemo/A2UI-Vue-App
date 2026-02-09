# A2UI Vue Demo

## 项目概述

本项目 `a2ui-vue-demo` 作为一个演示项目，展示了如何将 A2UI（Agent-to-User Interface）与 Vue.js 和 Lit 集成。根据 A2UI 技术报告，它展示了如何通过结合 Vue 3 的响应式特性与 Lit 的高效渲染能力来构建动态的、由代理驱动的用户界面。核心理念是通过 A2A 协议实现后端代理与前端 UI 之间的无缝通信，从而实时更新 UI 结构、数据模型和组件。

关键特性包括：
- **A2UI 桥接层**：用于处理 Vue 组件与 A2UI 处理器之间通信的层。
- **基于 Lit 的渲染**：利用 Lit 在 Vue 应用中渲染 A2UI 组件。
- **动态表面**：支持基于代理消息创建和更新 UI 表面。
- **集成模式**：演示 Shadow DOM 隔离、Light DOM 集成和通信桥接。

此演示基于 Vue 3 构建，依赖如 Pinia 用于状态管理和 Tailwind CSS 用于样式。它为构建 AI 代理驱动的应用提供了基础，支持模块化、可重用的 UI 组件。

## 安装指南

要设置项目，请按照以下步骤操作：

1. 克隆仓库：
   ```
   git clone <repository-url>
   cd a2ui-lit-vue
   ```

2. 使用 pnpm 安装依赖：
   ```
   pnpm install
   ```

   注意：本项目使用 pnpm 作为包管理器。如果您尚未安装 pnpm，可以通过 npm 安装：
   ```
   npm install -g pnpm
   ```

## 运行项目

依赖安装完成后，您可以使用 `package.json` 中定义的以下脚本运行项目：

- **开发服务器**：
  ```
  pnpm dev
  ```
  这将启动 Vite 开发服务器。在浏览器中打开 `http://localhost:5173`（或指定的端口）。

- **生产构建**：
  ```
  pnpm build
  ```
  这将为生产环境编译项目，输出文件到 `dist` 目录。

- **预览生产构建**：
  ```
  pnpm preview
  ```
  在本地服务生产构建以进行测试。

- **Linting**：
  ```
  pnpm lint
  ```
  在源文件上运行 ESLint 以检查代码质量问题。

## 依赖

项目依赖以下主要包（来自 `package.json`）：

### 运行时依赖
- `@microsoft/fetch-event-source`: ^2.0.1（用于处理服务器发送事件）
- `echarts`: ^5.5.0（图表库）
- `marked`: ^12.0.0（Markdown 解析器）
- `pinia`: ^2.1.7（Vue 的状态管理）
- `vue`: ^3.4.21（Vue.js 框架）
- `zod`: ^3.23.0（模式验证）

### 开发依赖
- `@vitejs/plugin-vue`: ^5.0.4（Vue 的 Vite 插件）
- `autoprefixer`: ^10.4.19（PostCSS 插件）
- `postcss`: ^8.4.38（CSS 处理器）
- `tailwindcss`: ^3.4.3（实用优先的 CSS 框架）
- `typescript`: ~5.4.0（TypeScript 支持）
- `vite`: ^5.2.0（构建工具）
- `vue-tsc`: ^2.0.6（Vue 的 TypeScript 编译器）

完整列表请参考 `package.json` 和 `pnpm-lock.yaml`。

## 项目结构

- `src/`：源代码目录
  - `components/`：Vue 组件
  - `composables/`：可重用组合函数
  - `core/`：A2UI 核心逻辑（例如桥接、处理器）
  - `stores/`：Pinia 存储
  - `styles/`：CSS 和 Tailwind 配置
  - `types/`：TypeScript 类型定义
- `server/`：后端相关文件（如果适用）
- `A2UI_Technical_Report.md`：A2UI 集成的详细技术文档。

## 贡献

欢迎贡献！请 fork 仓库并提交 pull request 您的更改。确保您的代码遵循项目的 linting 规则并包含相关测试。

## 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件（如果可用）。

更多深入的技术细节，请参考 [A2UI 技术报告](A2UI_Technical_Report.md)。