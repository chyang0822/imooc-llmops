# FunctionCallAgent 单元测试

## 测试文件位置

`test/internal/agent/test_function_call_agent.py`

## 测试覆盖范围

### 单元测试 (TestFunctionCallAgent)

1. **test_agent_initialization** - 测试Agent初始化
   - 验证LLM、配置和name字段正确设置
   - 验证Agent图结构已构建

2. **test_agent_has_name_field** - 测试name字段
   - 验证Agent有name属性
   - 验证name值为"agent"

3. **test_build_agent_creates_graph** - 测试图构建
   - 验证_build_agent方法创建了图结构
   - 验证图有invoke方法

4. **test_preset_operation_node_without_review** - 测试预设操作（无审核）
   - 验证无审核时返回空消息列表

5. **test_preset_operation_node_with_keyword_review** - 测试预设操作（有审核）
   - 验证包含敏感词时返回预设响应
   - 验证返回AIMessage类型

6. **test_tools_condition_without_tool_calls** - 测试工具条件（无工具调用）
   - 验证无工具调用时返回"__end__"

7. **test_tools_condition_with_tool_calls** - 测试工具条件（有工具调用）
   - 验证有工具调用时返回"tools"

8. **test_preset_operation_condition_with_ai_message** - 测试预设条件（AI消息）
   - 验证AI消息时返回"__end__"

9. **test_preset_operation_condition_with_human_message** - 测试预设条件（人类消息）
   - 验证人类消息时返回"long_term_memory_recall"

10. **test_max_iteration_count_exceeded** - 测试迭代次数限制
    - 验证超过最大迭代次数的检测

11. **test_agent_config_fields** - 测试Agent配置字段
    - 验证所有配置字段正确设置

12. **test_agent_state_initialization** - 测试Agent状态初始化
    - 验证状态对象正确初始化

13. **test_agent_with_empty_tools** - 测试空工具列表
    - 验证Agent可以使用空工具列表

14. **test_agent_queue_manager_property** - 测试队列管理器
    - 验证队列管理器属性存在
    - 验证有listen和publish方法

### 集成测试 (TestFunctionCallAgentIntegration)

1. **test_agent_graph_structure** - 测试图结构
   - 验证图结构正确
   - 验证图有invoke方法

2. **test_agent_serializable** - 测试可序列化性
   - 验证Agent继承自Serializable

3. **test_agent_runnable** - 测试Runnable接口
   - 验证Agent是Runnable实例

## 运行测试

### 运行所有测试
```bash
cd /Users/chyang/Documents/Notes/course_resources/LLM/【0】代码+PDF课件+电子书/imooc-llmops/api
pytest test/internal/agent/test_function_call_agent.py -v
```

### 运行特定测试类
```bash
pytest test/internal/agent/test_function_call_agent.py::TestFunctionCallAgent -v
```

### 运行特定测试方法
```bash
pytest test/internal/agent/test_function_call_agent.py::TestFunctionCallAgent::test_agent_initialization -v
```

### 运行集成测试
```bash
pytest test/internal/agent/test_function_call_agent.py::TestFunctionCallAgentIntegration -v
```

### 生成覆盖率报告
```bash
pytest test/internal/agent/test_function_call_agent.py --cov=internal.core.agent.agents.function_call_agent --cov-report=html
```

## 测试依赖

- pytest
- unittest.mock (Python标准库)
- langchain_core
- langgraph

## Mock对象

### MockLanguageModel
模拟语言模型，提供以下方法：
- `stream(messages)` - 返回AIMessage
- `get_num_tokens_from_messages(messages)` - 返回10
- `get_pricing()` - 返回(0.001, 0.002, 1000)
- `bind_tools(tools)` - 返回self

## 注意事项

1. 所有测试都使用Mock来隔离AgentQueueManager
2. 测试使用fixture来创建可重用的对象
3. 测试覆盖了主要的业务逻辑路径
4. 集成测试验证了Agent的接口契约

## 扩展测试

如需添加更多测试，可以：

1. 添加更多的Mock工具测试
2. 测试错误处理路径
3. 测试流式输出功能
4. 测试长期记忆功能
5. 测试输出审核功能
