# A2UI 工程技术调研报告

## 目录
1. [项目概览](#一项目概览)
2. [工程架构分析](#二工程架构分析)
3. [A2A 协议详解](#三a2a-协议详解)
4. [Lit 渲染器实现](#四lit-渲染器实现)
5. [核心技术路线](#五核心技术路线)
6. [Vue + Lit 集成方案](#六vue--lit-集成方案)
7. [实现步骤](#七实现步骤)
8. [技术挑战与建议](#八技术挑战与建议)

---

## 一、项目概览

### 1.1 背景
A2UI (Agent-to-User Interface) 是 Google 推出的开源生成式 UI 项目，允许 AI Agent 通过声明式 JSON 格式描述 UI，客户端使用原生组件库渲染。

### 1.2 核心理念
- **安全如数据，表达如代码**：Agent 发送声明式数据格式，而非可执行代码
- **LLM 友好**：扁平组件列表 + ID 引用，易于 Transformer 生成
- **平台无关**：同一 JSON 可在 Web、Flutter、移动端等多平台渲染
- **流式渲染**：支持渐进式 UI 更新，提供快速响应体验

### 1.3 当前状态
- 版本：v0.8 (公共预览版)
- 许可证：Apache 2.0
- 状态：规范仍在演进中，API 可能有变化

---

## 二、工程架构分析

### 2.1 目录结构

```
A2UI/
├── specification/              # A2UI 协议规范
│   ├── v0_8/              # v0.8 规范
│   │   ├── docs/             # 协议文档
│   │   └── json/             # JSON Schema 定义
│   │       ├── server_to_client.json
│   │       ├── client_to_server.json
│   │       └── standard_catalog_definition.json
│   └── v0_9/              # v0.9 规范（预览）
│
├── renderers/                # 渲染器实现
│   ├── web_core/           # 核心类型定义和消息处理器
│   │   └── src/v0_8/
│   │       ├── types/        # TypeScript 类型定义
│   │       ├── data/         # 数据处理核心
│   │       └── styles/      # 样式定义
│   ├── lit/                 # Lit Web Components 渲染器
│   │   └── src/
│   │       ├── 0.8/
│   │       │   ├── ui/          # Lit 组件实现
│   │       │   ├── data/        # Signal-based 数据处理器
│   │       │   ├── events/      # 事件处理
│   │       │   └── context/     # Lit Context
│   ├── angular/             # Angular 渲染器
│   └── flutter/             # Flutter 渲染器
│
├── a2a_agents/               # A2A 协议代理实现
│   ├── python/                 # Python Agent SDK
│   │   └── a2ui_agent/
│   │       └── src/a2ui/extension/
│   │           ├── a2ui_extension.py
│   │           └── send_a2ui_to_client_toolset.py
│   └── java/                   # Java Agent SDK
│
├── samples/                  # 示例应用
│   ├── agent/                 # Agent 示例
│   │   └── adk/
│   │       ├── restaurant_finder/    # 餐厅查找 Agent
│   │       ├── contact_lookup/      # 联系人查找
│   │       └── orchestrator/       # 编排器示例
│   └── client/                # 客户端示例
│       └── lit/shell/         # Lit Shell 示例应用
│
└── docs/                     # 文档
```

### 2.2 三大核心要素

#### 1. 组件树 (The Structure)
- 由 `surfaceUpdate` 消息定义的抽象组件树
- 使用**邻接表模型**：扁平列表 + ID 引用
- 避免嵌套 JSON 生成困难，便于 LLM 流式输出

#### 2. 数据模型 (The State)
- 由 `dataModelUpdate` 消息管理的 JSON 对象
- 支持路径绑定：`/user/name`（绝对路径）、`./textField`（相对路径）
- 支持初始化简写：同时设置默认值并绑定到路径

#### 3. 组件注册表 (The Catalog)
- 客户端定义的组件类型到原生组件的映射
- 标准目录：`https://github.com/google/A2UI/blob/main/specification/v0_8/json/standard_catalog_definition.json`
- 支持自定义目录：通过 `inlineCatalogs` 或 `componentRegistry.register()`

---

## 三、A2A 协议详解

### 3.1 通信模型

```
┌─────────────┐                    ┌─────────────┐
│   Agent    │                    │   Client    │
│  (Server)  │                    │  (Browser)  │
└─────┬──────┘                    └──────┬──────┘
      │                                  │
      │  1. SSE Connection (JSONL)        │
      ├────────────────────────────────────────>│
      │                                  │
      │  2. surfaceUpdate                 │
      ├────────────────────────────────────────>│
      │  3. dataModelUpdate              │
      ├────────────────────────────────────────>│
      │  4. beginRendering               │
      ├────────────────────────────────────────>│
      │                                  │ 5. UI Rendered
      │<──────────────────────────────────────┤
      │                                  │
      │               6. userAction        │
      │<──────────────────────────────────────┤
      │                                  │
      │  7. Process & Update UI          │
      ├────────────────────────────────────────>│
      │                                  │
└───────────────────────────────────────────┘
```

### 3.2 消息类型

#### 服务器到客户端 (JSONL Stream)

**1. surfaceUpdate** - 组件更新
```json
{
  "surfaceUpdate": {
    "surfaceId": "main",
    "components": [{
      "id": "root",
      "component": {
        "Column": {
          "children": {
            "explicitList": ["header", "content"]
          }
        }
      }
    }, {
      "id": "header",
      "component": {
        "Text": {
          "text": { "literalString": "欢迎使用" },
          "usageHint": "h1"
        }
      }
    }]
  }
}
```

**2. dataModelUpdate** - 数据模型更新
```json
{
  "dataModelUpdate": {
    "surfaceId": "main",
    "path": "user",
    "contents": [
      { "key": "name", "valueString": "张三" },
      { "key": "email", "valueString": "zhangsan@example.com" }
    ]
  }
}
```

**3. beginRendering** - 开始渲染
```json
{
  "beginRendering": {
    "surfaceId": "main",
    "catalogId": "https://github.com/google/A2UI/blob/main/specification/v0_8/json/standard_catalog_definition.json",
    "root": "root",
    "styles": {
      "primaryColor": "#00BFFF",
      "font": "Roboto"
    }
  }
}
```

**4. deleteSurface** - 删除 Surface
```json
{
  "deleteSurface": {
    "surfaceId": "temp-surface"
  }
}
```

#### 客户端到服务器 (A2A Message)

**userAction** - 用户操作
```json
{
  "userAction": {
    "name": "submit_form",
    "surfaceId": "main",
    "sourceComponentId": "submit_btn",
    "timestamp": "2025-01-28T10:00:00Z",
    "context": {
      "formData": {
        "name": "张三",
        "email": "zhangsan@example.com"
      }
    }
  }
}
```

### 3.3 Catalog 协商流程

```
1. Server 端声明能力 (Agent Card)
   └─ supportedCatalogIds: ["standard-catalog", "custom-catalog"]
   └─ acceptsInlineCatalogs: true

2. Client 端声明支持能力 (每个消息)
   └─ a2uiClientCapabilities:
       ├─ supportedCatalogIds: ["standard-catalog"]
       └─ inlineCatalogs: [...]

3. Server 选择 Catalog (beginRendering)
   └─ catalogId: "standard-catalog"

4. Client 渲染
   └─ 使用指定 Catalog 的组件定义
```

---

## 四、Lit 渲染器实现

### 4.1 核心架构

```typescript
┌─────────────────────────────────────────────────────┐
│             @a2ui/lit Package               │
├─────────────────────────────────────────────────────┤
│                                              │
│  ┌────────────┐                              │
│  │ web_core  │  核心类型和处理器                │
│  │ - Types    │                              │
│  │ - Guards   │                              │
│  │ - Model    │  A2uiMessageProcessor           │
│  └────────────┘                              │
│         ↓                                     │
│  ┌────────────┐                              │
│  │ lit/0.8    │  Lit 渲染层                 │
│  ├────────────┤                              │
│  │            │                              │
│  │ ┌────────┐ │                              │
│  │ │ Data   │ │  Signal-based 状态管理          │
│  │ │        │ │  - SignalMap                  │
│  │ │        │ │  - SignalArray                │
│  │ └────────┘ │                              │
│  │            │                              │
│  │ ┌────────┐ │                              │
│  │ │ UI     │ │  Lit Web Components            │
│  │ │        │ │  - Root                      │
│  │ │        │ │  - Surface                    │
│  │ │        │ │  - Card, Row, Column, Text...  │
│  │ └────────┘ │                              │
│  │            │                              │
│  │ ┌────────┐ │                              │
│  │ │Events │ │  事件处理系统                  │
│  │ └────────┘ │                              │
│  └────────────┘                              │
└─────────────────────────────────────────────────────┘
```

### 4.2 关键类解析

#### A2uiMessageProcessor (消息处理器)

位置：`renderers/web_core/src/v0_8/data/model-processor.ts`

核心职责：
1. **消息分发**：处理四种消息类型
2. **Surface 管理**：维护多个独立 Surface
3. **组件树构建**：从扁平列表递归构建树结构
4. **数据绑定解析**：支持绝对/相对路径
5. **模板渲染**：支持动态列表 `template` 渲染

关键方法：
```typescript
class A2uiMessageProcessor {
  // 处理消息流
  processMessages(messages: ServerToClientMessage[]): void

  // 获取组件数据（支持路径绑定）
  getData(node, relativePath, surfaceId): DataValue | null

  // 设置组件数据（支持路径绑定）
  setData(node, relativePath, value, surfaceId): void

  // 路径解析
  resolvePath(path, dataContextPath): string

  // 获取所有 Surface
  getSurfaces(): ReadonlyMap<string, Surface>
}
```

#### Signal-based 数据层

位置：`renderers/lit/src/0.8/data/signal-model-processor.ts`

特点：
- 使用 `@lit-labs/signals` 实现响应式
- SignalMap/SignalArray/SignalObject 自动触发更新
- 与 Lit 的 `SignalWatcher` 无缝集成

```typescript
export function createSignalA2uiMessageProcessor() {
  return new A2uiMessageProcessor({
    arrayCtor: SignalArray as unknown as ArrayConstructor,
    mapCtor: SignalMap as unknown as MapConstructor,
    objCtor: SignalObject as unknown as ObjectConstructor,
    setCtor: SignalSet as unknown as SetConstructor,
  });
}
```

#### Root 组件

位置：`renderers/lit/src/0.8/ui/root.ts`

核心职责：
1. **组件树渲染**：递归渲染子组件
2. **自定义组件支持**：通过 `componentRegistry` 注册
3. **事件传递**：将 processor 传递给子组件
4. **Light DOM 渲染**：使用 `render()` API

关键特性：
```typescript
@customElement("a2ui-root")
export class Root extends SignalWatcher(LitElement) {
  @property()
  accessor processor: A2uiMessageProcessor | null = null;

  @property()
  accessor childComponents: AnyComponentNode[] | null = null;

  // 渲染组件树
  private renderComponentTree(components: AnyComponentNode[]): TemplateResult {
    return html`${map(components, (component) => {
      // 1. 检查自定义组件
      if (this.enableCustomElements) {
        const elCtor = componentRegistry.get(component.type);
        if (elCtor) {
          return this.renderCustomComponent(component, elCtor);
        }
      }

      // 2. 渲染标准组件
      switch (component.type) {
        case "Text": return this.renderText(node);
        case "Button": return this.renderButton(node);
        // ... 其他组件
      }
    })}`;
  }
}
```

#### ComponentRegistry (组件注册表)

位置：`renderers/lit/src/0.8/ui/component-registry.ts`

功能：
- 注册自定义组件类型
- 生成 inline catalog
- 与 customElements API 集成

```typescript
class ComponentRegistry {
  register(
    typeName: string,
    constructor: CustomElementConstructorOf<HTMLElement>,
    tagName?: string,
    schema?: unknown
  ) {
    this.registry.set(typeName, constructor);
    if (schema) {
      this.schemas.set(typeName, schema);
    }
    // 自动注册为 Web Component
    customElements.define(tagName || `a2ui-custom-${typeName.toLowerCase()}`, constructor);
  }

  getInlineCatalog(): { components: {...} } {
    // 返回供 Server 使用的 catalog 定义
  }
}
```

### 4.3 标准组件清单

| 组件类型 | 用途 | 核心属性 |
|---------|------|-----------|
| **Text** | 文本显示 | text, usageHint (h1-h5, caption, body) |
| **Image** | 图片 | url, fit (contain/cover/fill), usageHint |
| **Icon** | 图标 | name (预定义图标集) |
| **Button** | 按钮 | child, action, primary |
| **TextField** | 文本输入 | label, text, textFieldType, validationRegexp |
| **CheckBox** | 复选框 | label, value |
| **DateTimeInput** | 日期时间 | value, enableDate, enableTime |
| **MultipleChoice** | 多选 | options, selections, maxAllowedSelections |
| **Slider** | 滑块 | value, minValue, maxValue |
| **Row** | 水平布局 | children (explicitList/template), alignment, distribution |
| **Column** | 垂直布局 | children, alignment, distribution |
| **List** | 列表 | children, direction (vertical/horizontal) |
| **Card** | 卡片容器 | child |
| **Tabs** | 标签页 | tabItems (title + child) |
| **Modal** | 模态框 | entryPointChild, contentChild |
| **Divider** | 分割线 | axis (horizontal/vertical) |
| **AudioPlayer** | 音频播放器 | url, description |
| **Video** | 视频 | url |

---

## 五、核心技术路线

### 5.1 数据流架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    A2UI 完整数据流                    │
└─────────────────────────────────────────────────────────────────┘

1. Agent 生成阶段
   ┌─────────────┐
   │   LLM       │ 生成 A2UI JSON (工具调用)
   └──────┬──────┘
          ↓
   ┌─────────────┐
   │ Validation  │ JSON Schema 验证
   └──────┬──────┘
          ↓
   ┌─────────────┐
   │   A2A       │ 转换为 A2A Part
   └──────┬──────┘
          ↓

2. 传输阶段
   ┌─────────────────┐
   │    SSE Stream   │ JSONL 格式流式传输
   └──────┬──────────┘
          ↓

3. 客户端处理
   ┌─────────────┐
   │ JSONL Parser │ 逐行解析
   └──────┬──────┘
          ↓
   ┌──────────────────────┐
   │ MessageProcessor    │ 路由到对应处理器
   └──────┬─────────────┘
          ↓
          ├── surfaceUpdate → Component Buffer
          ├── dataModelUpdate → Data Model
          ├── beginRendering → Trigger Render
          └── deleteSurface → Remove Surface

4. 渲染阶段
   ┌──────────────────────┐
   │ Component Tree Build │ 递归构建组件树
   └──────┬─────────────┘
          ↓
   ┌──────────────────────┐
   │ Data Binding       │ 解析数据绑定
   └──────┬─────────────┘
          ↓
   ┌──────────────────────┐
   │ Widget Registry     │ 映射到 Lit 组件
   └──────┬─────────────┘
          ↓
   ┌──────────────────────┐
   │ Lit Rendering      │ Shadow DOM / Light DOM
   └──────────────────────┘

5. 交互阶段
   ┌──────────────────────┐
   │ User Interaction  │ 点击、输入等
   └──────┬─────────────┘
          ↓
   ┌──────────────────────┐
   │ Context Resolve    │ 解析 action.context
   └──────┬─────────────┘
          ↓
   ┌──────────────────────┐
   │ A2A UserAction    │ 发送到 Agent
   └──────────────────────┘
```

### 5.2 依赖关系图

```
@a2ui/web_core (v0.8.0)
    ├─ types: TypeScript 类型定义
    ├─ guards: 类型守卫
    ├─ model-processor: 核心消息处理器
    └─ styles: 样式定义
         ↓
@a2ui/lit (v0.8.1)
    ├─ 依赖 @a2ui/web_core
    ├─ lit ^3.3.1
    ├─ @lit-labs/signals ^0.1.3
    ├─ @lit/context ^1.1.4
    └─ signal-utils ^0.21.1
         ↓
@a2a-js/sdk (A2A 协议客户端)
    ├─ 负责 A2A 通信
    └─ 处理 userAction 发送
```

---

## 六、Vue + Lit 集成方案

### 6.1 集成架构

```
┌─────────────────────────────────────────────────────────┐
│              Vue + Lit 混合架构                    │
└─────────────────────────────────────────────────────────┘

┌────────────┐         ┌──────────────────────┐
│    Vue     │         │    Lit Components    │
│  App Shell │         │   (@a2ui/lit)     │
└──────┬─────┘         └──────────┬───────────┘
       │                          │
       │ 1. 接收用户输入           │
       ├────────────────────────────>│
       │                          │
       │ 2. 构建消息             │
       │  ┌────────────────┐         │
       │  │ A2UIClient   │         │
       │  │ (包装层)    │         │
       │  └────────┬─────┘         │
       │           │               │
       └───────────┼──────────────>│ 3. 发送到 Agent
                   │               │
                   │               │
       ┌───────────┼───────────────┤ 4. 接收响应
       │           │               │
       ↓           ↓               ↓
   ┌──────────────────────────────────────────┐
   │  Vue 组件 (Vue 3 Composition API)      │
   │  - 管理应用状态                     │
   │  - 提供自定义 UI                   │
   │  - 业务逻辑层                       │
   └──────┬─────────────────────────────┘
          │
          │ 5. 渲染 A2UI Surface
          │
          ↓
   ┌──────────────────────────────────────────┐
   │  <a2ui-surface>                     │
   │  (Lit Web Component)                │
   │  - 自动处理 A2UI 协议             │
   │  - 渲染 Agent 生成的 UI           │
   └──────────────────────────────────────────┘
```

### 6.2 三种集成模式

#### 模式 1: Shadow DOM 隔离（推荐）

```vue
<template>
  <div class="app-container">
    <!-- Vue 管理的部分 -->
    <header>
      <MyHeader />
    </header>

    <!-- A2UI Surface (Shadow DOM 隔离) -->
    <a2ui-surface
      ref="a2uiSurface"
      :surface="a2uiSurfaceData"
      :processor="messageProcessor"
      @a2uiaction="handleA2UIAction"
    />

    <!-- Vue 管理的部分 -->
    <footer>
      <MyFooter />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { createSignalA2uiMessageProcessor } from '@a2ui/lit';
import '@a2ui/lit/ui/ui'; // 注册所有 Lit 组件

const a2uiSurface = ref();
const messageProcessor = createSignalA2uiMessageProcessor();
const a2uiSurfaceData = ref(null);

// 接收 A2UI 消息
const handleA2UIMessages = (messages) => {
  messageProcessor.processMessages(messages);
  a2uiSurfaceData.value = messageProcessor.getSurfaces().get('main');
};

const handleA2UIAction = (event) => {
  // 处理 A2UI 事件，通过 A2A 发送到 Agent
  console.log('A2UI Action:', event.detail);
};
</script>
```

**优点：**
- 样式完全隔离
- 无命名冲突
- 组件生命周期独立

#### 模式 2: Light DOM 集成

```vue
<template>
  <div class="app-container">
    <a2ui-root
      ref="a2uiRoot"
      :processor="messageProcessor"
      :childComponents="componentTree"
      enable-custom-elements="true"
    />
  </div>
</template>

<script setup lang="ts">
// Light DOM 模式，Vue 和 Lit 共享 DOM
// 可以用 Vue 的样式覆盖 Lit 组件样式
</script>
```

**优点：**
- 样式可覆盖
- DOM 可访问性更好
- 性能稍优

#### 模式 3: 通信桥接（高级）

```typescript
// a2ui-bridge.ts
export class A2UIBridge {
  private processor = createSignalA2uiMessageProcessor();
  private eventBus = mitt();

  // Vue 调用
  sendToAgent(message: string) {
    return this.a2aClient.send(message);
  }

  // Agent 返回 → 处理 → 通知 Vue
  handleAgentResponse(messages) {
    this.processor.processMessages(messages);
    this.eventBus.emit('a2ui-update', this.processor.getSurfaces());
  }

  // 监听 A2UI 事件 → 通知 Vue
  on(event: string, handler: Function) {
    this.eventBus.on(event, handler);
  }
}

// Vue 使用
const bridge = new A2UIBridge();
bridge.on('a2ui-update', (surfaces) => {
  // 更新 Vue 状态
});
```

### 6.3 数据流集成

```typescript
// 1. Vue 状态 → A2UI 消息
const vueState = reactive({
  user: { name: '', email: '' }
});

// 转换为 A2UI 格式并发送
const submitToAgent = async () => {
  const messages = [{
    dataModelUpdate: {
      surfaceId: 'main',
      path: 'user',
      contents: [
        { key: 'name', valueString: vueState.user.name },
        { key: 'email', valueString: vueState.user.email }
      ]
    }
  }];
  
  const response = await bridge.send(messages);
  
  // 2. A2UI 响应 → Vue 状态
  const surfaces = bridge.handleAgentResponse(response);
  // 更新 Vue 状态
  a2uiSurfaceData.value = surfaces.get('main');
};
```

---

## 七、实现步骤

### 阶段 1: 项目初始化 (1-2 天)

#### 1.1 创建 Vue 3 项目
```bash
npm create vue@latest a2ui-vue-demo
cd a2ui-vue-demo
npm install
```

#### 1.2 安装依赖
```bash
# A2UI 核心库
npm install @a2ui/lit

# A2A 协议 SDK
npm install @a2a-js/sdk

# 可选：Vite 插件
npm install @vitejs/plugin-vue
```

#### 1.3 项目结构
```
src/
├── components/              # Vue 组件
│   ├── AppHeader.vue
│   ├── AppFooter.vue
│   └── a2ui-bridge/    # A2UI 桥接层
│       ├── index.ts
│       └── client.ts
│
├── composables/           # 组合式函数
│   ├── useA2UI.ts
│   └── useAgent.ts
│
├── agents/               # Agent 集成
│   └── python-backend/
│       └── server.py
│
├── views/
│   └── Home.vue
│
├── App.vue
└── main.ts
```

### 阶段 2: 核心 A2UI 集成 (2-3 天)

#### 2.1 创建 A2UI 桥接层

`src/components/a2ui-bridge/index.ts`:
```typescript
import { createSignalA2uiMessageProcessor } from '@a2ui/lit';
import { v0_8 } from '@a2ui/lit';

export interface A2UIBridgeOptions {
  serverUrl?: string;
  surfaceId?: string;
}

export class A2UIBridge {
  private processor = createSignalA2uiMessageProcessor();
  private a2aClient: any = null;
  private surfaceId: string;

  constructor(options: A2UIBridgeOptions) {
    this.surfaceId = options.surfaceId || 'default-surface';
  }

  async initialize(serverUrl: string) {
    // 初始化 A2A 客户端
    // 参考: samples/client/lit/shell/client.ts
    const { A2AClient } = await import('@a2a-js/sdk');
    this.a2aClient = await A2AClient.fromCardUrl(
      `${serverUrl}/.well-known/agent-card.json`,
      {
        fetchImpl: async (url, init) => {
          const headers = new Headers(init?.headers);
          headers.set('X-A2A-Extensions', 'https://a2ui.org/a2a-extension/a2ui/v0.8');
          return fetch(url, { ...init, headers });
        }
      }
    );
  }

  getProcessor() {
    return this.processor;
  }

  processMessages(messages: v0_8.Types.ServerToClientMessage[]) {
    this.processor.processMessages(messages);
    return this.processor.getSurfaces().get(this.surfaceId) || null;
  }

  async sendUserAction(action: v0_8.Types.UserAction) {
    if (!this.a2aClient) throw new Error('A2A client not initialized');

    const response = await this.a2aClient.sendMessage({
      messageId: crypto.randomUUID(),
      role: 'user',
      parts: [{
        kind: 'data',
        data: { userAction: action },
        mimeType: 'application/json+a2ui'
      }]
    });

    // 处理响应
    if ('result' in response) {
      const messages = response.result.status.message?.parts
        ?.filter(p => p.kind === 'data')
        ?.map(p => p.data) || [];

      return this.processMessages(messages);
    }
  }
}
```

#### 2.2 创建 Vue Composable

`src/composables/useA2UI.ts`:
```typescript
import { ref, computed, onUnmounted } from 'vue';
import { A2UIBridge } from '@/components/a2ui-bridge';
import { v0_8 } from '@a2ui/lit';

export function useA2UI(serverUrl?: string) {
  const bridge = new A2UIBridge({
    surfaceId: 'main-surface'
  });
  
  const surface = ref<v0_8.Types.Surface | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isReady = computed(() => !!surface.value);

  // 初始化
  const initialize = async () => {
    try {
      loading.value = true;
      await bridge.initialize(serverUrl);
      console.log('A2UI Bridge initialized');
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  // 处理 A2UI 消息
  const handleMessages = (messages: v0_8.Types.ServerToClientMessage[]) {
    const newSurface = bridge.processMessages(messages);
    surface.value = newSurface;
  };

  // 发送用户操作
  const sendAction = async (action: v0_8.Types.UserAction) => {
    try {
      loading.value = true;
      await bridge.sendUserAction(action);
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  };

  // 清理
  onUnmounted(() => {
    // 清理资源
  });

  return {
    bridge,
    surface,
    loading,
    error,
    isReady,
    initialize,
    handleMessages,
    sendAction
  };
}
```

#### 2.3 在 Vue 组件中使用

`src/views/Home.vue`:
```vue
<template>
  <div class="home-container">
    <header>
      <h1>Vue + A2UI Demo</h1>
      <div class="status" v-if="loading">加载中...</div>
      <div class="error" v-if="error">{{ error }}</div>
    </header>

    <!-- A2UI Surface -->
    <main class="a2ui-wrapper">
      <a2ui-surface
        v-if="surface"
        :surface="surface"
        :processor="bridge.getProcessor()"
        @a2uiaction="handleA2UIAction"
        enable-custom-elements="true"
      />
      <div v-else class="placeholder">
        等待 Agent 生成 UI...
      </div>
    </main>

    <!-- 控制面板 -->
    <aside class="controls">
      <h3>控制面板</h3>
      <button @click="sendTestMessage">发送测试消息</button>
      <button @click="clearSurface">清除 Surface</button>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useA2UI } from '@/composables/useA2UI';
import '@a2ui/lit/ui/ui'; // 注册所有 Lit 组件
import { v0_8 } from '@a2ui/lit';

// 使用 Composable
const {
  bridge,
  surface,
  loading,
  error,
  isReady,
  initialize,
  handleMessages,
  sendAction
} = useA2UI('http://localhost:10002');

// 生命周期
onMounted(async () => {
  await initialize();
  
  // 发送初始请求
  sendTestMessage();
});

// 发送测试消息
const sendTestMessage = async () => {
  const testMessages: v0_8.Types.ServerToClientMessage[] = [
    {
      surfaceUpdate: {
        surfaceId: 'main-surface',
        components: [{
          id: 'root',
          component: {
            Column: {
              children: {
                explicitList: ['header', 'content']
              }
            }
          }
        }, {
          id: 'header',
          component: {
            Text: {
              text: { literalString: '欢迎使用 Vue + A2UI' },
              usageHint: 'h1'
            }
          }
        }, {
          id: 'content',
          component: {
            Card: {
              child: 'text-content'
            }
          }
        }, {
          id: 'text-content',
          component: {
            Text: {
              text: { literalString: '这是一个由 Agent 生成的 UI' },
              usageHint: 'body'
            }
          }
        }]
      }
    }, {
      dataModelUpdate: {
        surfaceId: 'main-surface',
        path: 'user',
        contents: [{
          key: 'greeting',
          valueString: '你好！'
        }]
      }
    }, {
      beginRendering: {
        surfaceId: 'main-surface',
        root: 'root',
        styles: {
          primaryColor: '#00BFFF',
          font: 'system-ui'
        }
      }
    }
  ];

  handleMessages(testMessages);
};

// 处理 A2UI 动作
const handleA2UIAction = (event: CustomEvent) => {
  const action = event.detail as v0_8.Types.UserAction;
  console.log('收到 A2UI Action:', action);
  
  // 发送到 Agent
  sendAction(action);
};

const clearSurface = () => {
  surface.value = null;
};
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.a2ui-wrapper {
  flex: 1;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  margin: 20px 0;
}

.placeholder {
  text-align: center;
  padding: 60px;
  color: #999;
}

.controls {
  padding: 20px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
}

button {
  margin: 8px 0;
  padding: 8px 16px;
  cursor: pointer;
}
</style>
```

### 阶段 3: 后端 Agent (2-3 天)

#### 3.1 创建 Python Agent

`agents/python-backend/server.py`:
```python
import asyncio
from google.adk import Agent
from google.adk.agents import LlmAgent
from google.adk.tools import SendA2uiToClientToolset
from google.adk.models import GeminiModel

# A2UI Schema（从 A2UI 工程复制）
A2UI_SCHEMA = {
    "title": "A2UI Message Schema",
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "surfaceUpdate": { ... },
            "dataModelUpdate": { ... },
            "beginRendering": { ... }
        }
    }
    }
}

async def create_agent():
    """创建带 A2UI 支持的 Agent"""
    
    agent = LlmAgent(
        model=GeminiModel(
            model_name="gemini-2.0-flash-exp",
            api_key="your-gemini-api-key"
        ),
        instruction=(
            "你是一个 UI 生成助手。"
            "使用 A2UI 协议生成响应式 UI。"
            "支持中文输出。"
        ),
        tools=[
            SendA2uiToClientToolset(
                a2ui_enabled=True,
                a2ui_schema=A2UI_SCHEMA
            )
        ]
    )
    
    return agent

if __name__ == "__main__":
    agent = asyncio.run(create_agent())
    print("Agent 已启动，监听端口 10002...")
    # 启动 A2A 服务
```

### 阶段 4: 样式定制 (1 天)

#### 4.1 覆盖默认样式

`src/styles/a2ui-overrides.css`:
```css
/* 覆盖 A2UI Lit 组件样式 */
a2ui-surface {
  --primary-color: #00BFFF;
  --font-family: 'PingFang SC', system-ui;
}

a2ui-card {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

a2ui-button button {
  background: var(--primary-color);
  border-radius: 20px;
  font-weight: 500;
}

a2ui-text.h1 {
  font-size: 2rem;
  font-weight: 700;
}
```

### 阶段 5: 测试与优化 (2-3 天)

#### 5.1 单元测试

```typescript
// tests/composables/useA2UI.test.ts
import { describe, it, expect, vi } from 'vitest';
import { useA2UI } from '@/composables/useA2UI';

describe('useA2UI', () => {
  it('should initialize bridge', async () => {
    const { bridge, initialize } = useA2UI();
    await initialize();
    expect(bridge).toBeDefined();
  });

  it('should process messages', () => {
    const { handleMessages, surface } = useA2UI();
    const messages = [{ /* A2UI message */ }];
    handleMessages(messages);
    expect(surface.value).not.toBeNull();
  });
});
```

#### 5.2 端到端测试

```bash
# 1. 启动后端 Agent
cd agents/python-backend
python server.py

# 2. 启动 Vue 前端
npm run dev

# 3. 测试流程
# - 打开 http://localhost:5173
# - 发送测试消息
# - 验证 UI 渲染
# - 测试用户交互
# - 检查事件发送
```

---

## 八、技术挑战与建议

### 8.1 主要挑战

#### 1. 样式隔离冲突
**问题**：Lit Shadow DOM 与 Vue 样式可能有冲突

**解决方案**：
```css
/* 使用 CSS 自定义属性传递 */
a2ui-surface {
  --a2ui-primary-color: var(--vue-primary-color);
  --a2ui-font-family: var(--vue-font-family);
}
```

#### 2. 状态同步
**问题**：Vue 响应式数据与 Lit Signal 同步

**解决方案**：
```typescript
// 使用 Lit 的 effect 监听变化
import { effect } from '@lit-labs/signals';

effect(() => {
  const surfaces = processor.getSurfaces();
  // 触发 Vue 更新
  emit('a2ui-update', surfaces);
});
```

#### 3. 事件冒泡
**问题**：A2UI 事件需要正确传递到 Vue

**解决方案**：
```vue
<template>
  <a2ui-surface
    @a2uiaction="handleA2UIAction"
  />
</template>

<script setup>
const handleA2UIAction = (event: CustomEvent) => {
  // event.detail 包含 action 数据
  const action = event.detail;
  // 处理事件
};
</script>
```

### 8.2 最佳实践

#### 1. 组件注册
- 在 `main.ts` 统一注册所有 Lit 组件
- 使用 `enableCustomElements="true"` 启用自定义组件

#### 2. 性能优化
- 使用 `v-once` 避免不必要的重新渲染
- 对于复杂 UI，考虑使用 `requestIdleCallback` 分批渲染

#### 3. 类型安全
```typescript
// 严格类型检查
const messages: v0_8.Types.ServerToClientMessage[] = [...];
const surface: v0_8.Types.Surface | null = null;
```

#### 4. 错误处理
```typescript
try {
  await bridge.sendUserAction(action);
} catch (error) {
  console.error('A2UI Error:', error);
  // 显示用户友好的错误消息
  showErrorToast(error.message);
}
```

### 8.3 扩展建议

#### 1. 自定义组件
```typescript
import { ComponentRegistry } from '@a2ui/lit/ui';

// 注册自定义 Vue-Lite 混合组件
componentRegistry.register('VueChart', VueChartComponent, 'vue-chart', {
  type: 'object',
  properties: {
    data: { type: 'object' },
    type: { type: 'string', enum: ['line', 'bar', 'pie'] }
  }
});
```

#### 2. 国际化支持
```typescript
// 在 A2UI Schema 中支持 i18n
const i18nSchema = {
  components: {
    Text: {
      properties: {
        text: {
          $ref: '#/definitions/LocalizedString'
        }
      }
    }
  }
};
```

---

## 九、总结与展望

### 9.1 关键要点

1. **A2UI 核心价值**：
   - 声明式 UI 生成
   - LLM 友好的协议
   - 平台无关的渲染

2. **Lit 渲染器优势**：
   - Shadow DOM 隔离
   - 高性能 Web Components
   - 完整的 A2UI 实现

3. **Vue 集成策略**：
   - 通过桥接层解耦
   - 利用 Composition API
   - 保持响应式优势

### 9.2 技术路线图

```
Phase 1: MVP (2周)
  ├─ 基础集成
  ├─ 标准 UI 渲染
  └─ 简单交互

Phase 2: 增强功能 (3周)
  ├─ 自定义组件
  ├─ 样式定制
  └─ 错误处理

Phase 3: 高级特性 (4周)
  ├─ 多 Surface 支持
  ├─ 复杂交互
  └─ 性能优化

Phase 4: 生产化 (2周)
  ├─ 测试覆盖
  ├─ 文档完善
  └─ 部署优化
```

### 9.3 参考资源

- [A2UI 官方仓库](https://github.com/google/A2UI)
- [A2UI 协议文档](https://github.com/google/A2UI/tree/main/specification/v0_8/docs)
- [Lit 官方文档](https://lit.dev/)
- [Vue 3 文档](https://vuejs.org/)
- [A2A 协议](https://a2a.org/)

---

**报告完成日期**：2026-02-04
**A2UI 版本**：v0.8
**Vue 版本**：3.x
**技术栈**：Vue 3 + TypeScript + Vite + Lit Web Components
