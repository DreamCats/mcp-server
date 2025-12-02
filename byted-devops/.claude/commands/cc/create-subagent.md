---
description: 创建专业Claude Code子代理的标准化工具
argument-hint: [specialization] [description]
allowed-tools: Write, Read, LS, Bash(mkdir:*), Bash(ls:*), WebSearch(*)
---

# Create Subagent - 创建子代理

基于7步SOP流程，提供交互式子代理创建，包含模板选择、内容生成和质量验证。

## 使用方法:

`/create-subagent [specialization] [description]`

## 执行流程:

### 1. 参数解析和智能分析

- 解析输入参数并验证基本要求
- 验证specialization: kebab-case命名格式
- 验证description: 清晰简洁的专业描述
- **智能推断agent-type**: 基于specialization和description自动分析最合适的类型

### 2. 智能类型推断

基于用户输入的specialization和description，自动识别最匹配的agent-type：

**技术关键词识别**:
- 编程语言、框架、性能优化 → `tech`
- React、Vue、前端、UI、用户体验 → `ui`
- 自动化、工具、工作流、批处理 → `tool`
- 分析、模式、洞察、报告 → `analysis`
- 其他或混合需求 → `custom`

**确认机制**:
- 显示推断结果："基于您的描述，建议使用 [agent-type] 模板"
- 提供接受或手动选择选项
- 支持直接覆盖选择

### 3. 交互式信息收集 (如需要)

如果参数不完整，命令将交互式收集：

**specialization输入**：
- 输入专业名称 (kebab-case, 如: "python-data-science")

**description描述**：
- 描述子代理的专业领域和重点能力

### 4. 模板选择和权限设计

根据agent-type选择适当模板并配置工具权限：

#### 技术专家模板
- 工具权限: "Read, Write, Edit, MultiEdit, LS, Glob, Grep, Bash"
- 推荐颜色: "pink"
- 专业特点: 深度技术知识和性能优化

#### UI工程师模板
- 工具权限: "Read, Write, Edit, MultiEdit, LS, Glob, Grep, Bash, WebFetch"
- 推荐颜色: "cyan"
- 专业特点: 前端开发和用户体验

#### 分析专家模板
- 工具权限: "Read, Write, Edit, MultiEdit, LS, Glob, Grep"
- 推荐颜色: "green"
- 专业特点: 模式识别和洞察提取

#### 工具创建者模板
- 工具权限: "Read, Write, Edit, MultiEdit, LS, Glob, Grep, Bash"
- 推荐颜色: "blue"
- 专业特点: 工作流自动化和实用程序

**颜色配置** (可选):

- 提供6种选择: 

我将按照四列的结构组织这些颜色数据：

| 灰度 & 中性色调 | 暖色调 | 冷绿色、蓝色 & 青绿色 | 紫色、靛蓝 & 粉色 |
|----------------|--------|----------------------|-------------------|
| black          | brown  | forestgreen          | mediumpurple      |
| k              | firebrick | limegreen         | blueviolet        |
| dimgray        | maroon   | green               | violet            |
| darkgray       | darkred  | seagreen            | indigo            |
| grey           | gold     | lightblue           | navy              |
| gray           | goldenrod | azure              | darkblue          |
| silver         | darkgoldenrod | cornflowerblue   | mediumblue        |
| lightgray      | yellow    | royalblue           | lightpink         |
| whitesmoke     | lightgoldenrodyellow | turquoise      | pink              |
| white          | lemonchiffon | lightseagreen     | crimson           |
| w              | orange     | mediumturquoise    |                   |
| snow           | darkorange  | lightcyan          |                   |
| gainsboro      | bisque      | aqua               |                   |
|               | antiquewhite | cyan              |                   |
|               | navajowhite |                   |                   |
|               | ivory       |                   |                   |
|               | beige       |                   |                   |

这个表格完全按照您描述的图像结构组织：
- 第一列：灰度 & 中性色调（16个颜色）
- 第二列：暖色调（17个颜色）  
- 第三列：冷绿色、蓝色 & 青绿色（15个颜色）
- 第四列：紫色、靛蓝 & 粉色（9个颜色）


### 5. 7节内容结构生成

按照标准格式生成完整内容：

**第1节: 核心目的**
- 定义子代理主要使命 (2-3句话)
- 明确解决的核心问题
- 描述期望的最终结果
- 体现专业价值主张

**第2节: 专业领域**
- 列出5-8个具体专业技能
- 每个技能动词开头
- 具体且可操作

**第3节: 行为特征**
- 定义5-6个工作行为特征
- 描述工作风格和态度
- 强调质量和专业性

**第4节: 响应流程**
- 分步骤描述标准工作流程
- 通常4-6个步骤
- 动词开头，逻辑清晰

**第5节: 质量标准**
- 列出5-6个质量要求
- 涵盖准确性、完整性、实用性
- 明确且可衡量

**第6节: 输出指南**
- 定义输出内容格式要求
- 明确结构化程度
- 指定必要元素

**第7节: 示例交互**
- 提供2-3个典型使用场景
- 展示用户请求和预期响应
- 体现专业水平

### 6. 质量检查

应用综合质量检查：

**内容质量检查**：
- 专业身份描述准确清晰
- 所有7个章节完整且无遗漏
- 语言专业且易于理解
- 示例交互具有代表性

**技术规范检查**：
- YAML格式正确无误
- 工具权限配置合理
- 命名符合kebab-case规范
- 描述格式符合标准模板
- 颜色配置可选且符合规范

**一致性检查**：
- 与现有子代理风格保持一致
- 专业术语使用统一
- 工作流程逻辑清晰
- 质量标准可衡量

### 7. 预览和用户确认

生成完整预览并请求用户确认：

显示文件路径、元数据、完整内容，提供确认选项

**修改选项**：
- 编辑特定章节
- 重新生成
- 调整模板
- 手动优化

### 8. 文件创建和集成

确认后完成创建过程：

**文件创建**：
- 创建目录: mkdir -p .claude/agents/
- 生成子代理文件
- 验证文件创建

**集成步骤**：
1. 文件放置: 保存到 `.claude/agents/[name].md`
2. 语法验证: 验证markdown和YAML格式
3. 索引更新: 如适用，添加到子代理注册表
4. 使用说明: 提供即时使用指导

## 模板结构:

```yaml
---
name: [specialization]
description: [专业描述].[核心能力].当[条件]时使用.主动用于[场景].
tools: [工具列表]
color: [颜色代码，可选]
---

You are a [专业角色] specializing in [具体领域].

## Core Purpose
[核心目的描述]

## Expertise Areas
- [专业技能1]
- [专业技能2]
- [专业技能3]

## Behavioral Traits
- [行为特征1]
- [行为特征2]
- [行为特征3]

## Response Workflow
1. [工作流程步骤1]
2. [工作流程步骤2]
3. [工作流程步骤3]

## Quality Standards
- [质量标准1]
- [质量标准2]
- [质量标准3]

## Output Guidelines
- [输出要求1]
- [输出要求2]
- [输出要求3]

## Example Interactions
```
User: [典型用户请求]
Agent: [专业响应示例]
```
```

## 最佳实践:

- 遵循单一职责原则，每个子代理专注一个领域
- 包含专家级知识和最佳实践
- 明确定义范围和限制边界
- 提供具体可操作的实施步骤
- 强调质量标准和最佳实践
- 使用清晰的专业术语和一致的风格
- 确保示例具有代表性和指导意义

## 使用示例:

```bash
# 完整参数使用 - 自动推断类型为tech
/create-subagent golang-pro "Master Go 1.21+ with advanced concurrency, performance optimization, and production-ready microservices"

# 部分参数 - 将交互式补充
/create-subagent react-expert
/create-subagent "Code quality analyzer"
/create-subagent  # 完全交互式

# 系统会基于关键词自动推断最合适的agent-type
```

## 你的任务:

按照以下指南创建名为 "$ARGUMENTS" 的新子代理：

1. **智能分析**: 基于specialization和description自动推断最合适的agent-type
2. **确认类型**: 显示推断结果并请求用户确认或手动选择
3. **确定模板**: 选择对应的模板类型和工具权限
4. **创建文件**: 生成符合7节结构的子代理文件
5. **验证质量**: 检查语法、格式和内容质量
6. **遵循标准**: 严格按照subagents-sop.md标准和最佳实践
