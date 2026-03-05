# AGENTS.md - Factory Droid 全场景规范

> **Factory Droid** 是一个全自动闭环管理的 Mission 执行系统，支持 规划 -> 并行执行 -> 验证验收 -> 自省修复 的完整工作流。

---

## 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [Droids 规范](#droids-规范)
4. [Commands 命令体系](#commands-命令体系)
5. [Skills 技能系统](#skills-技能系统)
6. [Hooks 钩子系统](#hooks-钩子系统)
7. [通用规则](#通用规则)
8. [场景规范](#场景规范)
9. [执行模式](#执行模式)
10. [状态管理](#状态管理)
11. [日志规范](#日志规范)
12. [最佳实践](#最佳实践)

---

## 快速开始

### 启动 Mission

使用快捷命令激活 Auto Missions 工作模式：

```
/auto-missions [你的任务]
```

**示例**：
```
/auto-missions 写一篇 5000 字关于 Agentic AI 的技术报告
/auto-missions 实现一个博客系统，包含用户认证和文章管理
/auto-missions 调研当前主流的 AI 编程助手
```

**启动后自动执行**：
1. 激活 Missions 工作模式
2. 识别场景（写作/编程/调研）
3. 启动 Backbone 主干代理
4. 自动拆解 Milestones 和 Features
5. 并行分发任务给 Branch 代理
6. Validator 自动验收每个 Milestone

---

## 系统架构

### 核心组件

```
Factory Droid
├── Droids (代理)
│   ├── Backbone    - 主干代理，负责任务规划和调度
│   ├── Branch      - 分支代理，执行具体任务
│   └── Validator   - 验证代理，质量把关和验收
├── Commands (命令)
│   ├── /auto-missions - 启动自动新任务
│   ├── /mission-status     - 查看状态
│   ├── /mission-logs       - 查看日志
│   ├── /mission-pause      - 暂停执行
│   ├── /mission-resume     - 恢复执行
│   └── /mission-show-plan  - 显示规划
├── Skills (技能)
│   ├── common      - 通用技能
│   ├── programming - 编程技能
│   ├── writing     - 写作技能
│   └── research    - 调研技能
└── Hooks (钩子)
    ├── load-mission-state.sh   - 加载状态
    ├── save-mission-state.sh   - 保存状态
    ├── log-mission-event.sh    - 记录日志
    ├── notify-milestone.sh     - 通知事件
    └── format-output.sh        - 格式化输出
```

### 状态管理

所有 Mission 状态持久化在 `.factory/mission-state.json`：

```json
{
  "mission_goal": "任务目标",
  "status": "in-progress",
  "current_milestone": 1,
  "parallel_execution": true,
  "max_parallel_workers": 3,
  "milestones": [...],
  "logs": [...]
}
```

---

## Droids 规范

### Backbone（主干代理）

**核心职责**：管理整个 Mission 的生命周期，实现全自动闭环工作模式。

**阶段一：规划模式**（当 status 为 "planning" 时）
1. **状态检查**：读取 `mission-state.json`
2. **需求分析与自动拆解**：
   - 读取 `mission_goal` 以及上下文信息
   - 自主思考合理的执行步骤
   - 将目标分解为 3-8 个 Milestones，每个 Milestone 下划分具体 Features
3. **异构模型交叉验收 (Cross-Model Critique)**：
   - 制定初步规划后，派发给 Validator 进行"规划漏洞审查"
   - 根据反馈补全边界条件、遗漏依赖和性能隐患
   - 形成优化后的终版规划
4. **无缝衔接**：
   - 将终版规划写入 `mission-state.json`
   - 更新状态从 "planning" 到 "in-progress"
   - 直接进入第一里程碑执行

**阶段二：执行模式**（当 status 为 "in-progress" 时）
1. **任务分派与角色设定**：
   - 定位尚未完成的 Features
   - 通过 Task 工具派发给 Branch 代理
   - 明确告知 Branch 应扮演的角色、任务和涉及文件
2. **并行能力提升**：
   - 如果配置允许，并行执行无依赖的 Features
3. **验证与自我修复闭环**：
   - Milestone 完成后，派发给 Validator 验收
   - PASS: 更新 Milestone 状态为 "completed"，进入下一阶段
   - FAIL: 分析失败原因，动态加入修复 Feature，重新调度
   - retry_count 达到 max_retries 时，状态改为 "paused"，向用户报错

**输出格式**：
```markdown
【当前场景】：xxx
【Mission 状态】：进行中 / 第 N 个 Milestone

Milestones:
- [ ] Milestone 1（成功标准：...）
  Features: ...
  当前进度：xx%

当前进度：XX%
```

---

### Branch（分支代理）

**核心职责**：根据 Backbone 指令，执行指定的单个或一组相关联的任务（Feature）。

**工作流程**：
1. **理解上下文**：审阅任务说明，包括角色设定、任务目标、涉及文件
2. **反思与设计**：构建技术思路/修改清单，避免盲目修改
3. **执行指令**：
   - 编程任务：读取源码、编辑代码、运行测试
   - 写作/调研任务：搜集信息、编写内容、检查一致性
4. **盲测交付**：完成后写清楚改变内容并交付
5. **交付成果输出**

**输出格式**：
```
✓ DONE: [Feature 名称或简介]
- 扮演角色：[前端/后端/调研/写作...]
- 完成内容：[简要描述实质性改变]
- 影响文件：[列出相关文件]
- 风险说明：[潜在隐患]
```

**角色设定示例**：
- **technical-writer**: 技术文档编写
- **senior-technical-writer**: 高级技术文档编写
- **validator**: 质量验证
- **senior-python-developer**: 高级 Python 开发
- **frontend-developer**: 前端开发

---

### Validator（验证代理）

**核心职责**：作为异构模型交叉验证器，对规划和成果进行严格审查。

**反派把关人身份**：
- 永远不要假设对方产出的规划是严谨的或代码是无 Bug 的
- 打破认知和编程习惯上的同质化盲区
- 唯一能对方案或成果 "放行" 的角色

**工作流程**：
1. **获取待测标准**：读取 success_criteria 或审查要求
2. **多维度核验**：
   - **规划/设计审查**：核实计划闭环、边界条件、性能瓶颈、安全隐患
   - **编程任务**：阅读代码逻辑、执行测试命令、验证逻辑正确性
   - **写作/调研**：核对需求覆盖、结构化完整性
3. **输出结论报告**

**输出格式（PASS）**：
```markdown
### CONCLUSION: PASS
- **检查点 1**：✓ [证据，比如测试全部通过或文字符合要求]
- **检查点 2**：✓ [证据]
```

**输出格式（FAIL）**：
```markdown
### CONCLUSION: FAIL
- **检查点 1**：✗ [哪里失败了，比如哪个单测没通过或什么文档缺失]
- **检查点 2**：✓ 通过
- **修复建议**：[具体的修复动作]
```

---

## Commands 命令体系

### `/auto-missions` - 启动 Auto Mission
**参数**：`<任务描述>`

启动一个全新的 Autonomous Mission 工作流。

**示例**：
```
/auto-missions 实现一个博客系统
```

---

### `/mission-status` - 查看状态
显示当前 Mission 的执行进度、并行执行状态和闭环修复状态。

**输出内容**：
- 基本信息（目标、状态、并行配置）
- Milestones 进度结构
- 验证和自修复信息
- 并行节点占用

**示例**：
```text
╔════════════════════════════════════════╗
║         📊 Mission 状态面板             ║
╠════════════════════════════════════════╣
║  目标：根据当前工程配置重新编写 AGENTS.MD  ║
║  状态：🟢 in-progress                   ║
║  并行执行：开启，支持 3 个并发             ║
╚════════════════════════════════════════╝

📍 当前 Milestone 进度 [2]/[5]:
   名称：设计文档新架构
   状态：⟳ in-progress
```

---

### `/mission-logs` - 查看日志
**参数**：
- 可选：日志数量（默认 20 条）
- 可选：日志级别（INFO/WARN/ERROR）

查看 Mission 的详细执行日志。

**日志级别**：
- **INFO**: 正常执行信息，任务开始/完成、状态变更
- **WARN**: 警告信息，质量问题、潜在问题
- **ERROR**: 错误信息，执行失败、验证失败

**示例**：
```
/mission-logs       # 查看最近 20 条日志
/mission-logs 50    # 查看最近 50 条日志
/mission-logs WARN  # 查看所有 WARN 级别日志
```

---

### `/mission-pause` - 暂停执行
暂停当前正在执行的 Mission，保存当前状态以便后续恢复。

**暂停时记录**：
- 当前 Milestone 和 Feature
- 执行上下文
- checkpoint 数据

---

### `/mission-resume` - 恢复执行
从暂停点恢复 Mission 执行。

**恢复逻辑**：
1. 读取 checkpoint_data
2. 判断暂停位置
3. 从 Feature、验证或下一个 Milestone 继续

---

### `/mission-show-plan` - 显示规划
显示当前 Mission 的详细规划信息。

**输出内容**：
- Mission 目标
- 当前状态
- 所有 Milestones（含进度）
- 每个 Milestone 下的 Features

---

## Skills 技能系统

### 技能分类

#### Common（通用技能）
- **dynamic-skill-generator**: 动态生成新技能
- **plan-milestones**: 规划 Milestones 和 Features
- **validate-output**: 验证输出格式

#### Programming（编程技能）
- **code-implement**: 实现功能代码 + 编写测试
- **test-coverage**: 确保测试覆盖率 ≥ 85%

#### Writing（写作技能）
- **long-form-article**: 撰写 3000+ 字深度长文
- **seo-optimize**: 优化 SEO（关键词、元数据、结构）

#### Research（调研技能）
- **competitor-analysis**: 竞品/技术方案对比调研
- **literature-summary**: 文献/资料总结

---

### 动态技能生成

**触发条件**：
- 现有 Skills 无法满足任务需求
- 任务需要高度专业化知识
- 多次尝试使用通用 Worker 失败
- 用户明确要求创建新技能

**生成流程**：
1. 识别技能缺口
2. 使用 `dynamic-skill-generator` 生成技能定义
3. 创建 `.factory/skills/custom/[skill-name].md`
4. 更新 mission-state.json.skills_used
5. 重新执行任务，使用新技能

**技能定义模板**：
```markdown
---
name: [skill-name]
description: [简短描述]
user-invocable: true
---

# [Skill Display Name]

## 功能描述
[详细描述]

## 工作流程
1. [步骤 1]
2. [步骤 2]

## 质量标准
- ✓ [标准 1]
- ✓ [标准 2]
```

---

## Hooks 钩子系统

### 事件触发

Hooks 在以下事件触发：
- **SessionStart**: 会话开始时
- **SubagentStart**: Subagent 启动时
- **SubagentStop**: Subagent 停止时
- **PostToolUse**: 使用 Edit/Write 工具后

### 钩子脚本

| 钩子 | 功能 |
|------|------|
| `load-mission-state.sh` | 加载 mission-state.json |
| `save-mission-state.sh` | 保存 mission-state.json |
| `log-mission-event.sh` | 记录日志事件 |
| `notify-milestone.sh` | 发送 Milestone 通知 |
| `format-output.sh` | 格式化输出内容 |

### 配置方式

在 `settings.json` 中配置：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "command": "bash \"$FACTORY_PROJECT_DIR/.factory/hooks/load-mission-state.sh\""
      }
    ],
    "SubagentStart": [
      {
        "matcher": "backbone|branch|validator",
        "command": "echo '{\"level\": \"INFO\", \"source\": \"$DROID\"}' | bash ..."
      }
    ]
  }
}
```

---

## 通用规则

所有 Subagents 必须遵守以下通用规则：

1. **输出结构化**：所有输出必须包含清晰的结构（大纲 + 内容 + 验证）
2. **保持一致性**：使用相同的格式和术语，便于解析
3. **明确进度**：使用 TodoWrite 工具实时显示进度
4. **质量第一**：完成任务后必须进行自我验证
5. **文档完整**：所有修改必须包含清晰的说明

---

## 场景规范

### 写作场景规范

**输出格式**：
```markdown
# [标题]

## 大纲
1. 章节 1
   - 子要点
2. 章节 2

## 内容
[完整内容...]

## 统计信息
- 字数：XXXX 字
- 预估字数：XXXX 字
- 完成度：XX%
```

**质量标准**：
- ✓ 必须先输出大纲
- ✓ 字数统计准确
- ✓ 包含字数预估
- ✓ 进行 SEO 检查
- ✓ 结构清晰，层次分明
- ✓ 语言流畅，适合发布

**SEO 检查清单**：
- 标题包含主关键词
- 合理使用 H1-H3 标题
- 段落长度适中（100-150 词）
- 关键词密度 1-2%
- 包含内部/外部链接
- 图像有 alt 文本

---

### 编程场景规范

**输出格式**：
```markdown
✓ 功能实现完成

**修改文件**：
- `src/feature.ts` (新增 XXX 行)
- `tests/feature.test.ts` (新增 XX 行)

**测试结果**：
- 测试通过：X/X
- 覆盖率：XX%

**代码质量**：
- Lint 检查：通过
- 类型检查：通过
```

**质量标准**：
- ✓ 测试覆盖率 ≥ 85%
- ✓ 核心业务逻辑覆盖率 ≥ 95%
- ✓ 通过所有单元测试
- ✓ 通过 Lint 检查
- ✓ 代码符合项目规范
- ✓ 包含必要的注释和文档

**测试要求**：
- 测试正常路径
- 测试边界条件
- 测试异常情况
- 测试可重复执行
- 测试运行快速（< 5 秒）

---

### 调研场景规范

**输出格式**：
```markdown
# [调研主题] 调研报告

## Findings（研究发现）
[总结关键发现...]

## Sources（数据来源）
- [来源标题](URL) - 访问时间：2026-MM-DD
- ...

## Recommendations（建议）
1. 建议 1
2. 建议 2

## 对比表格
| 维度 | 方案 A | 方案 B | 方案 C |
|------|--------|--------|--------|
| ... | ... | ... | ... |
```

**质量标准**：
- ✓ 所有结论必须标注来源
- ✓ 每条来源包含访问时间（2026 年）
- ✓ 使用 WebSearch 验证最新信息
- ✓ 数据准确，来源可靠
- ✓ 观点客观，避免偏见
- ✓ 包含明确的推荐和理由

**信息时效性**：
- 优先使用 2025-2026 年数据
- 明确标注数据发布时间
- 对于过时信息，说明原因

---

## 执行模式

### 并行执行

**并行模式**：
- `auto` - 自动分析依赖关系，最大化并行
- `parallel` - 尽可能并行执行
- `sequential` - 串行执行

**依赖管理**：
- 每个 Feature 可声明 dependencies
- 使用拓扑排序确定执行顺序
- 等待所有依赖完成后才执行

**资源限制**：
- `max_parallel_workers` 控制并发数
- 默认 3 个并发 Worker
- 可根据系统资源调整

**示例**：
```json
{
  "parallel_execution": true,
  "max_parallel_workers": 3,
  "milestones": [
    {
      "features": [
        {"id": "1.1", "dependencies": []},
        {"id": "1.2", "dependencies": []},
        {"id": "1.3", "dependencies": ["1.1"]}
      ]
    }
  ]
}
```

---

### 动态技能生成

**使用场景**：
1. 当前已有的 Skills 无法满足任务需求
2. 任务需要高度专业化的知识或流程
3. 多次尝试使用通用 Worker 失败
4. 用户或 Orchestrator 明确需要新技能

**完整流程**：
1. **需求分析**：识别当前任务的具体需求
2. **技能设计**：定义技能名称、描述、工具、工作流程
3. **技能创建**：在 `.factory/skills/custom/` 目录下创建 SKILL.md
4. **注册更新**：在 mission-state.json 中添加技能名称
5. **验证测试**：使用新技能执行简单测试任务

---

## 状态管理

### 中断恢复

**暂停命令**：`/mission-pause`
- 保存当前 checkpoint
- 记录正在执行的任务
- 支持精确恢复到中断点

**恢复命令**：`/mission-resume`
- 从 Feature、验证或下一个 Milestone 继续
- 重置执行上下文

**恢复逻辑**：
```
checkpoint_data.feature_id 存在且未完成 → 从该 Feature 继续
checkpoint_data.feature_id 存在且已完成 → 检查 Milestone 验证
只有 milestone_id → 从该 Milestone 开始
都没有 → 从 current_milestone 继续
```

---

### 重定向

**命令**：`/mission-redirect [指令]`

**支持类型**：
- 功能调整（添加/删除/修改功能）
- 方向改变（架构调整）
- 优先级调整（重新排序）
- Milestone 调整（合并/拆分）

**使用示例**：
```
/mission-redirect 添加用户管理功能，包括注册和登录
/mission-redirect 将数据库从 MySQL 改为 PostgreSQL
/mission-redirect 优先实现 API 接口，前端可以延后
```

---

## 日志规范

### 日志级别

| 级别 | 用途 | 示例 |
|------|------|------|
| **INFO** | 正常执行信息 | 任务开始/完成、状态变更 |
| **WARN** | 警告信息 | 测试覆盖率低、潜在问题 |
| **ERROR** | 错误信息 | 执行失败、验证失败 |
| **DEBUG** | 调试信息 | 详细操作、文件编辑 |

### 日志记录方式

**使用日志脚本**：
```bash
# INFO 级别
echo '{"level": "INFO", "source": "backbone", "message": "开始执行 Milestone 1"}' | bash log-mission-event.sh

# WARN 级别
echo '{"level": "WARN", "source": "validator", "message": "测试覆盖率不足", "extra_info": "当前：82%, 目标：85%"}' | bash log-mission-event.sh

# ERROR 级别
echo '{"level": "ERROR", "source": "branch", "message": "测试失败", "extra_info": "3 个测试用例失败"}' | bash log-mission-event.sh
```

### 日志格式

```
[时间戳] [级别] [来源] 消息
  - 额外信息（可选）
```

**示例输出**：
```text
[2026-03-03T10:45:00Z] [INFO] [backbone] Feature f3 "编写测试" 已派发执行
  - Worker: branch
  - Token 使用：12,345

[2026-03-03T10:25:00Z] [WARN] [validator] 测试覆盖率 82%，低于目标 85%
  - 建议：添加边界情况测试，要求开启 Repair
```

---

## 最佳实践

### 使用建议

1. **始终使用 TodoWrite**：实时显示进度
2. **保持沟通**：遇到问题及时报告
3. **自我验证**：完成任务后自行检查
4. **文档完整**：所有修改都有清晰说明
5. **质量优先**：不牺牲质量追求速度
6. **状态一致**：保持 mission-state.json 准确

### 性能优化

- 合理设置 `max_parallel_workers`，根据系统资源调整
- 使用依赖管理避免冲突
- 日志记录要快速，避免阻塞执行
- 只记录关键事件，避免过度记录

### 故障排除

**常见问题**：

| 问题 | 解决方案 |
|------|----------|
| Milestone 卡住 | 检查 mission-logs，使用 /mission-status 查看状态 |
| 测试失败 | 查看 Validator 反馈，修复失败用例 |
| 信息不足 | 请求用户补充信息 |
| 达到重试上限 | 使用 /mission-resume 重置 retry_count，或 /mission-redirect 调整方向 |

---

## 附录

### 文件结构

```
.factory/
├── mission-state.json          # Mission 状态
├── mission-state.json.example  # 状态模板
├── settings.json               # 配置设置
├── commands/                   # 命令定义
│   ├── missions.md
│   ├── status.md
│   └── ...
├── droids/                     # 代理定义
│   ├── backbone.md
│   ├── branch.md
│   └── validator.md
├── skills/                     # 技能定义
│   ├── common/
│   ├── programming/
│   ├── writing/
│   └── research/
└── hooks/                      # 钩子脚本
    ├── load-mission-state.sh
    ├── save-mission-state.sh
    └── ...
```

### 版本信息

- **规范版本**: 2.0
- **最后更新**: 2026-03-03
- **兼容系统**: Windows/Linux/macOS

---

*本文档由 Factory Droid 自动生成并维护*

