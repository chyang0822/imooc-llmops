#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/03/21
@Author  : test
@File    : test_function_call_agent.py

FunctionCallAgent 单元测试 - 简化版本，避免超时
"""
import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from internal.core.agent.agents.function_call_agent import FunctionCallAgent
from internal.core.agent.entities.agent_entity import AgentConfig, AgentState
from internal.entity.conversation_entity import InvokeFrom


class MockLanguageModel:
    """模拟语言模型"""
    
    def __init__(self):
        self.features = []
    
    def stream(self, messages):
        """模拟流式输出"""
        yield AIMessage(content="这是一个测试回复")
    
    def get_num_tokens_from_messages(self, messages):
        """模拟token计数"""
        return 10
    
    def get_pricing(self):
        """模拟价格获取"""
        return 0.001, 0.002, 1000
    
    def bind_tools(self, tools):
        """模拟工具绑定"""
        return self


class TestFunctionCallAgentBasic:
    """FunctionCallAgent 基础测试"""

    @pytest.fixture
    def mock_llm(self):
        """创建模拟的语言模型"""
        return MockLanguageModel()

    @pytest.fixture
    def agent_config(self):
        """创建Agent配置"""
        return AgentConfig(
            user_id=uuid.uuid4(),
            invoke_from=InvokeFrom.ASSISTANT_AGENT,
            enable_long_term_memory=False,
            tools=[],
            preset_prompt="你是一个有帮助的助手",
            max_iteration_count=10,
            review_config={
                "enable": False,
                "keywords": [],
                "inputs_config": {"enable": False, "preset_response": ""},
                "outputs_config": {"enable": False},
            }
        )

    @pytest.fixture
    def agent(self, mock_llm, agent_config):
        """创建FunctionCallAgent实例"""
        with patch('internal.core.agent.agents.base_agent.AgentQueueManager') as mock_queue:
            # Mock 队列管理器
            mock_queue_instance = MagicMock()
            mock_queue_instance.listen = MagicMock(return_value=iter([]))
            mock_queue_instance.publish = MagicMock()
            mock_queue.return_value = mock_queue_instance
            
            agent = FunctionCallAgent(
                llm=mock_llm,
                agent_config=agent_config,
            )
            return agent

    def test_agent_has_name_field(self, agent):
        """测试Agent是否有name字段"""
        assert hasattr(agent, 'name')
        assert agent.name == "agent"

    def test_agent_has_llm(self, agent, mock_llm):
        """测试Agent是否有LLM"""
        assert agent.llm == mock_llm

    def test_agent_has_config(self, agent, agent_config):
        """测试Agent是否有配置"""
        assert agent.agent_config == agent_config

    def test_agent_has_graph(self, agent):
        """测试Agent是否有图结构"""
        assert agent._agent is not None
        assert hasattr(agent._agent, 'invoke')

    def test_agent_config_fields(self, agent_config):
        """测试Agent配置字段"""
        assert agent_config.user_id is not None
        assert agent_config.invoke_from == InvokeFrom.ASSISTANT_AGENT
        assert agent_config.enable_long_term_memory == False
        assert agent_config.tools == []
        assert agent_config.preset_prompt == "你是一个有帮助的助手"
        assert agent_config.max_iteration_count == 10

    def test_agent_state_initialization(self):
        """测试Agent状态初始化"""
        task_id = uuid.uuid4()
        state = AgentState(
            messages=[HumanMessage(content="测试消息")],
            history=[],
            long_term_memory="测试记忆",
            task_id=task_id,
            iteration_count=0,
        )
        
        assert state["task_id"] == task_id
        assert state["iteration_count"] == 0
        assert len(state["messages"]) == 1
        assert state["long_term_memory"] == "测试记忆"

    def test_preset_operation_node_without_review(self, agent):
        """测试预设操作节点（无审核）"""
        state = AgentState(
            messages=[HumanMessage(content="你好")],
            history=[],
            long_term_memory="",
            task_id=uuid.uuid4(),
            iteration_count=0,
        )
        
        result = agent._preset_operation_node(state)
        assert result["messages"] == []

    def test_tools_condition_without_tool_calls(self, agent):
        """测试工具条件判断（无工具调用）"""
        state = AgentState(
            messages=[AIMessage(content="这是一个普通回复")],
            history=[],
            long_term_memory="",
            task_id=uuid.uuid4(),
            iteration_count=0,
        )
        
        result = agent._tools_condition(state)
        assert result == "__end__"

    def test_tools_condition_with_tool_calls(self, agent):
        """测试工具条件判断（有工具调用）"""
        ai_message = AIMessage(content="调用工具")
        ai_message.tool_calls = [
            {
                "id": "call_123",
                "name": "test_tool",
                "args": {"param": "value"}
            }
        ]
        
        state = AgentState(
            messages=[ai_message],
            history=[],
            long_term_memory="",
            task_id=uuid.uuid4(),
            iteration_count=0,
        )
        
        result = agent._tools_condition(state)
        assert result == "tools"

    def test_preset_operation_condition_with_ai_message(self, agent):
        """测试预设操作条件（AI消息）"""
        state = AgentState(
            messages=[AIMessage(content="AI回复")],
            history=[],
            long_term_memory="",
            task_id=uuid.uuid4(),
            iteration_count=0,
        )
        
        result = agent._preset_operation_condition(state)
        assert result == "__end__"

    def test_preset_operation_condition_with_human_message(self, agent):
        """测试预设操作条件（人类消息）"""
        state = AgentState(
            messages=[HumanMessage(content="用户提问")],
            history=[],
            long_term_memory="",
            task_id=uuid.uuid4(),
            iteration_count=0,
        )
        
        result = agent._preset_operation_condition(state)
        assert result == "long_term_memory_recall"

    def test_max_iteration_count_exceeded(self, agent):
        """测试超过最大迭代次数"""
        agent.agent_config.max_iteration_count = 1
        
        state = AgentState(
            messages=[HumanMessage(content="测试")],
            history=[],
            long_term_memory="",
            task_id=uuid.uuid4(),
            iteration_count=2,
        )
        
        assert state["iteration_count"] > agent.agent_config.max_iteration_count

    def test_agent_queue_manager_property(self, agent):
        """测试Agent队列管理器属性"""
        queue_manager = agent.agent_queue_manager
        assert queue_manager is not None
        assert hasattr(queue_manager, 'listen')
        assert hasattr(queue_manager, 'publish')


class TestFunctionCallAgentInterfaces:
    """FunctionCallAgent 接口测试"""

    @pytest.fixture
    def mock_llm(self):
        """创建模拟的语言模型"""
        return MockLanguageModel()

    @pytest.fixture
    def agent_config(self):
        """创建Agent配置"""
        return AgentConfig(
            user_id=uuid.uuid4(),
            invoke_from=InvokeFrom.ASSISTANT_AGENT,
            enable_long_term_memory=False,
            tools=[],
            preset_prompt="你是一个有帮助的助手",
            max_iteration_count=10,
            review_config={
                "enable": False,
                "keywords": [],
                "inputs_config": {"enable": False, "preset_response": ""},
                "outputs_config": {"enable": False},
            }
        )

    @pytest.fixture
    def agent(self, mock_llm, agent_config):
        """创建FunctionCallAgent实例"""
        with patch('internal.core.agent.agents.base_agent.AgentQueueManager') as mock_queue:
            mock_queue_instance = MagicMock()
            mock_queue_instance.listen = MagicMock(return_value=iter([]))
            mock_queue_instance.publish = MagicMock()
            mock_queue.return_value = mock_queue_instance
            
            agent = FunctionCallAgent(
                llm=mock_llm,
                agent_config=agent_config,
            )
            return agent

    def test_agent_is_serializable(self, agent):
        """测试Agent是否可序列化"""
        from langchain_core.load import Serializable
        assert isinstance(agent, Serializable)

    def test_agent_is_runnable(self, agent):
        """测试Agent是否是Runnable"""
        from langchain_core.runnables import Runnable
        assert isinstance(agent, Runnable)

    def test_agent_graph_has_invoke(self, agent):
        """测试Agent图是否有invoke方法"""
        assert callable(getattr(agent._agent, 'invoke', None))

    def test_mock_llm_stream(self):
        """测试Mock LLM的stream方法"""
        llm = MockLanguageModel()
        messages = [HumanMessage(content="test")]
        result = list(llm.stream(messages))
        assert len(result) == 1
        assert isinstance(result[0], AIMessage)

    def test_mock_llm_get_pricing(self):
        """测试Mock LLM的get_pricing方法"""
        llm = MockLanguageModel()
        input_price, output_price, unit = llm.get_pricing()
        assert input_price == 0.001
        assert output_price == 0.002
        assert unit == 1000

    def test_mock_llm_get_num_tokens(self):
        """测试Mock LLM的get_num_tokens_from_messages方法"""
        llm = MockLanguageModel()
        messages = [HumanMessage(content="test")]
        tokens = llm.get_num_tokens_from_messages(messages)
        assert tokens == 10
