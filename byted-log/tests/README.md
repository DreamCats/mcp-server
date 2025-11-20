# MCP服务器测试文档

## 概述

本文档描述了重构后的MCP服务器的测试策略和用例。测试覆盖了动态headers获取、每客户端会话隔离等核心功能。

## 测试数据

使用用户提供的真实测试数据：

- **Headers**: `CAS_SESSION_US="1865f510d37eb4cf2447d210cbf17686"`
- **LogID**: `02176355661407900000000000000000000ffff0a71b1e8a4db84`
- **PSM**: `ttec.script.live_promotion_change`
- **Region**: `us`

## 测试用例

### 1. 成功工作流测试 (`test_real_data_success_workflow`)

**目的**: 验证使用真实数据的成功查询流程

**测试步骤**:
1. 创建包含真实cookie的mock上下文
2. 模拟JWT认证管理器
3. 模拟成功的日志查询结果
4. 调用MCP工具函数
5. 验证返回结果格式和内容

**预期结果**:
- 返回成功的日志查询结果
- 包含正确的日志ID和PSM信息
- 使用区域特定的cookie进行认证

### 2. 缺失Cookie测试 (`test_real_data_missing_cookie`)

**目的**: 验证缺少认证信息时的错误处理

**测试步骤**:
1. 创建空的headers上下文
2. 调用MCP工具函数
3. 验证错误响应

**预期结果**:
- 返回明确的错误信息
- 提示用户需要提供Cookie认证信息

### 3. 区域特定Cookie优先级测试 (`test_real_data_region_specific_cookie_priority`)

**目的**: 验证区域特定cookie的优先级高于默认cookie

**测试步骤**:
1. 创建同时包含默认cookie和区域特定cookie的上下文
2. 调用MCP工具函数
3. 验证JWT管理器使用的cookie值

**预期结果**:
- 优先使用`COOKIE_US`而不是默认的`cookie`

### 4. 错误处理测试 (`test_real_data_error_handling`)

**目的**: 验证异常情况下的错误处理

**测试步骤**:
1. 创建包含真实cookie的上下文
2. 模拟认证失败的异常情况
3. 调用MCP工具函数
4. 验证错误响应

**预期结果**:
- 返回包含具体错误信息的响应
- 错误信息中包含异常详情

### 5. 多PSM服务测试 (`test_multiple_psm_services`)

**目的**: 验证多个PSM服务的解析和处理

**测试步骤**:
1. 创建包含多个PSM服务的请求
2. 调用MCP工具函数
3. 验证PSM列表的解析结果

**预期结果**:
- PSM列表被正确解析为数组格式
- 每个PSM服务都被正确处理

### 6. 工具注册测试 (`test_tool_registration`)

**目的**: 验证MCP工具正确注册

**测试步骤**:
1. 创建服务器实例
2. 验证工具存在性

**预期结果**:
- `query_logs_by_logid`工具已正确注册

## 运行测试

### 运行所有测试
```bash
python -m pytest tests/test_real_data_workflow.py -v
```

### 运行特定测试
```bash
python -m pytest tests/test_real_data_workflow.py::TestRealDataWorkflow::test_real_data_success_workflow -v
```

### 生成测试报告
```bash
python tests/run_tests.py
```

## 测试架构

### 测试文件结构
```
tests/
├── conftest.py              # 测试配置和共享工具函数
├── pytest.ini              # pytest配置文件
├── run_tests.py            # 测试运行器
└── test_real_data_workflow.py  # 主要测试用例
```

### 关键测试组件

1. **Mock Context**: 模拟MCP上下文对象，提供headers和session管理
2. **Mock JWT Manager**: 模拟JWT认证管理器，处理认证逻辑
3. **Mock Log Query**: 模拟日志查询服务，返回预设的查询结果
4. **Real Data Fixtures**: 提供用户测试数据的fixture

## 测试覆盖率

测试覆盖了以下关键场景：

- ✅ 成功查询流程
- ✅ 认证失败处理
- ✅ Cookie缺失处理
- ✅ 区域特定Cookie优先级
- ✅ 多PSM服务支持
- ✅ 异常处理机制
- ✅ 工具注册验证

## 注意事项

1. **异步测试**: 所有MCP工具调用都是异步的，测试需要使用`@pytest.mark.asyncio`
2. **Mock对象**: 使用`unittest.mock`来模拟外部依赖，确保测试的独立性
3. **FastMCP返回格式**: FastMCP返回的是`(content_list, metadata_dict)`格式的元组
4. **资源清理**: 当前设计中，异常发生时不会执行资源清理，只在成功路径执行

## 改进建议

1. **异常处理优化**: 考虑在异常处理中也执行资源清理
2. **更多边界测试**: 增加更多边界条件和异常情况的测试
3. **性能测试**: 添加性能相关的测试用例
4. **集成测试**: 在适当的时候添加真实的集成测试（不依赖mock）