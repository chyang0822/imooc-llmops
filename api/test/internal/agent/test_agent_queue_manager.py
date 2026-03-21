#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/03/21
@Author  : test
@File    : test_agent_queue_manager.py

AgentQueueManager 单元测试
"""
import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from queue import Queue

from internal.core.agent.agents.agent_queue_manager import AgentQueueManager
from internal.core.agent.entities.queue_entity import AgentThought, QueueEvent
from internal.entity.conversation_entity import InvokeFrom


class TestAgentQueueManagerBasic:
    """AgentQueueManager 基础测试"""

    @pytest.fixture
    def mock_redis(self):
        """创建模拟的 Redis 客户端"""
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.delete.return_value = 1
        return redis_mock

    @pytest.fixture
    def queue_manager(self, mock_redis):
        """创建 AgentQueueManager 实例"""
        with patch('internal.core.agent.agents.agent_queue_manager.injector') as mock_injector:
            mock_injector.get.return_value = mock_redis
            manager = AgentQueueManager(
                user_id=uuid.uuid4(),
                invoke_from=InvokeFrom.ASSISTANT_AGENT,
            )
            return manager

    def test_initialization(self, queue_manager):
        """测试 AgentQueueManager 初始化"""
        assert queue_manager.user_id is not None
        assert queue_manager.invoke_from == InvokeFrom.ASSISTANT_AGENT
        assert queue_manager._queues == {}
        assert queue_manager.redis_client is not None

    def test_queue_creation(self, queue_manager):
        """测试队列创建"""
        task_id = uuid.uuid4()
        q = queue_manager.queue(task_id)
        
        assert q is not None
        assert isinstance(q, Queue)
        assert str(task_id) in queue_manager._queues

    def test_queue_reuse(self, queue_manager):
        """测试队列重用"""
        task_id = uuid.uuid4()
        q1 = queue_manager.queue(task_id)
        q2 = queue_manager.queue(task_id)
        
        assert q1 is q2

    def test_publish_agent_thought(self, queue_manager):
        """测试发布 AgentThought"""
        task_id = uuid.uuid4()
        thought = AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.AGENT_MESSAGE,
            thought="测试思考",
        )
        
        queue_manager.publish(task_id, thought)
        
        # 从队列中获取发布的数据
        q = queue_manager.queue(task_id)
        retrieved_thought = q.get(timeout=1)
        
        assert retrieved_thought == thought

    def test_publish_error(self, queue_manager):
        """测试发布错误"""
        task_id = uuid.uuid4()
        error_msg = "测试错误"
        
        queue_manager.publish_error(task_id, error_msg)
        
        # 从队列中获取发布的数据
        q = queue_manager.queue(task_id)
        retrieved_thought = q.get(timeout=1)
        
        assert retrieved_thought.event == QueueEvent.ERROR
        assert retrieved_thought.observation == error_msg

    def test_stop_listen(self, queue_manager):
        """测试停止监听"""
        task_id = uuid.uuid4()
        queue_manager.stop_listen(task_id)
        
        # 从队列中获取停止信号
        q = queue_manager.queue(task_id)
        stop_signal = q.get(timeout=1)
        
        assert stop_signal is None

    def test_publish_with_stop_event(self, queue_manager):
        """测试发布停止事件"""
        task_id = uuid.uuid4()
        thought = AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.STOP,
        )
        
        queue_manager.publish(task_id, thought)
        
        # 从队列中获取发布的数据
        q = queue_manager.queue(task_id)
        retrieved_thought = q.get(timeout=1)
        assert retrieved_thought == thought
        
        # 应该有停止信号
        stop_signal = q.get(timeout=1)
        assert stop_signal is None

    def test_publish_with_error_event(self, queue_manager):
        """测试发布错误事件"""
        task_id = uuid.uuid4()
        thought = AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.ERROR,
            observation="错误信息",
        )
        
        queue_manager.publish(task_id, thought)
        
        # 从队列中获取发布的数据
        q = queue_manager.queue(task_id)
        retrieved_thought = q.get(timeout=1)
        assert retrieved_thought == thought
        
        # 应该有停止信号
        stop_signal = q.get(timeout=1)
        assert stop_signal is None

    def test_publish_with_timeout_event(self, queue_manager):
        """测试发布超时事件"""
        task_id = uuid.uuid4()
        thought = AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.TIMEOUT,
        )
        
        queue_manager.publish(task_id, thought)
        
        # 从队列中获取发布的数据
        q = queue_manager.queue(task_id)
        retrieved_thought = q.get(timeout=1)
        assert retrieved_thought == thought
        
        # 应该有停止信号
        stop_signal = q.get(timeout=1)
        assert stop_signal is None

    def test_publish_with_agent_end_event(self, queue_manager):
        """测试发布 Agent 结束事件"""
        task_id = uuid.uuid4()
        thought = AgentThought(
            id=uuid.uuid4(),
            task_id=task_id,
            event=QueueEvent.AGENT_END,
        )
        
        queue_manager.publish(task_id, thought)
        
        # 从队列中获取发布的数据
        q = queue_manager.queue(task_id)
        retrieved_thought = q.get(timeout=1)
        assert retrieved_thought == thought
        
        # 应该有停止信号
        stop_signal = q.get(timeout=1)
        assert stop_signal is None


class TestAgentQueueManagerCacheKeys:
    """AgentQueueManager 缓存键测试"""

    def test_generate_task_belong_cache_key(self):
        """测试生成任务专属缓存键"""
        task_id = uuid.uuid4()
        key = AgentQueueManager.generate_task_belong_cache_key(task_id)
        
        assert key == f"generate_task_belong:{str(task_id)}"

    def test_generate_task_stopped_cache_key(self):
        """测试生成任务停止缓存键"""
        task_id = uuid.uuid4()
        key = AgentQueueManager.generate_task_stopped_cache_key(task_id)
        
        assert key == f"generate_task_stopped:{str(task_id)}"

    def test_cache_key_uniqueness(self):
        """测试缓存键的唯一性"""
        task_id1 = uuid.uuid4()
        task_id2 = uuid.uuid4()
        
        key1 = AgentQueueManager.generate_task_belong_cache_key(task_id1)
        key2 = AgentQueueManager.generate_task_belong_cache_key(task_id2)
        
        assert key1 != key2


class TestAgentQueueManagerRedisIntegration:
    """AgentQueueManager Redis 集成测试"""

    @pytest.fixture
    def mock_redis(self):
        """创建模拟的 Redis 客户端"""
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        return redis_mock

    @pytest.fixture
    def queue_manager(self, mock_redis):
        """创建 AgentQueueManager 实例"""
        with patch('internal.core.agent.agents.agent_queue_manager.injector') as mock_injector:
            mock_injector.get.return_value = mock_redis
            manager = AgentQueueManager(
                user_id=uuid.uuid4(),
                invoke_from=InvokeFrom.WEB_APP,
            )
            return manager

    def test_queue_creation_sets_redis_key(self, queue_manager, mock_redis):
        """测试队列创建时设置 Redis 键"""
        task_id = uuid.uuid4()
        queue_manager.queue(task_id)
        
        # 验证 setex 被调用
        assert mock_redis.setex.called
        
        # 获取调用参数
        call_args = mock_redis.setex.call_args
        key = call_args[0][0]
        ttl = call_args[0][1]
        value = call_args[0][2]
        
        assert key == AgentQueueManager.generate_task_belong_cache_key(task_id)
        assert ttl == 1800
        assert "account" in value

    def test_is_stopped_checks_redis(self, queue_manager, mock_redis):
        """测试 _is_stopped 检查 Redis"""
        task_id = uuid.uuid4()
        
        # 模拟 Redis 返回 None（未停止）
        mock_redis.get.return_value = None
        assert queue_manager._is_stopped(task_id) == False
        
        # 模拟 Redis 返回值（已停止）
        mock_redis.get.return_value = b'1'
        assert queue_manager._is_stopped(task_id) == True

    def test_set_stop_flag_class_method(self, mock_redis):
        """测试 set_stop_flag 类方法"""
        with patch('internal.core.agent.agents.agent_queue_manager.injector') as mock_injector:
            mock_injector.get.return_value = mock_redis
            
            task_id = uuid.uuid4()
            user_id = uuid.uuid4()
            
            # 模拟任务已存在
            mock_redis.get.return_value = f"account-{str(user_id)}".encode()
            
            AgentQueueManager.set_stop_flag(
                task_id=task_id,
                invoke_from=InvokeFrom.WEB_APP,
                user_id=user_id,
            )
            
            # 验证 setex 被调用来设置停止标志
            assert mock_redis.setex.called


class TestAgentQueueManagerMultipleTasks:
    """AgentQueueManager 多任务测试"""

    @pytest.fixture
    def mock_redis(self):
        """创建模拟的 Redis 客户端"""
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        return redis_mock

    @pytest.fixture
    def queue_manager(self, mock_redis):
        """创建 AgentQueueManager 实例"""
        with patch('internal.core.agent.agents.agent_queue_manager.injector') as mock_injector:
            mock_injector.get.return_value = mock_redis
            manager = AgentQueueManager(
                user_id=uuid.uuid4(),
                invoke_from=InvokeFrom.ASSISTANT_AGENT,
            )
            return manager

    def test_multiple_tasks_independent_queues(self, queue_manager):
        """测试多个任务有独立的队列"""
        task_id1 = uuid.uuid4()
        task_id2 = uuid.uuid4()
        
        q1 = queue_manager.queue(task_id1)
        q2 = queue_manager.queue(task_id2)
        
        assert q1 is not q2
        assert len(queue_manager._queues) == 2

    def test_multiple_tasks_independent_data(self, queue_manager):
        """测试多个任务的数据独立"""
        task_id1 = uuid.uuid4()
        task_id2 = uuid.uuid4()
        
        thought1 = AgentThought(
            id=uuid.uuid4(),
            task_id=task_id1,
            event=QueueEvent.AGENT_MESSAGE,
            thought="任务1的思考",
        )
        
        thought2 = AgentThought(
            id=uuid.uuid4(),
            task_id=task_id2,
            event=QueueEvent.AGENT_MESSAGE,
            thought="任务2的思考",
        )
        
        queue_manager.publish(task_id1, thought1)
        queue_manager.publish(task_id2, thought2)
        
        # 从各自的队列中获取数据
        q1 = queue_manager.queue(task_id1)
        q2 = queue_manager.queue(task_id2)
        
        retrieved1 = q1.get(timeout=1)
        retrieved2 = q2.get(timeout=1)
        
        assert retrieved1.thought == "任务1的思考"
        assert retrieved2.thought == "任务2的思考"
