#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/03/21
@Author  : test
@File    : conftest.py
"""
import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker, scoped_session
from app.http.app import app as _app
from internal.extension.database_extension import db as _db


@pytest.fixture(scope="session")
def app():
    """获取Flask应用并返回"""
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    return _app


@pytest.fixture
def client(app):
    """获取Flask应用的测试客户端"""
    with app.test_client() as client:
        # 添加默认的授权令牌
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NmRiMzBkMS0zMTk5LTRlNzktYTBjZC1hYmYxMmZhNjg1OGYiLCJpc3MiOiJsbG1vcHMiLCJleHAiOjE3MzM1MDU2NTR9.HSKjINY58fzengY3BmxIDOnJyACnBnz9NmgVN3y02iI"
        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"
        yield client


@pytest.fixture
def db(app):
    """创建一个临时的数据库会话"""
    with app.app_context():
        # 1.获取数据库连接并创建事务
        connection = _db.engine.connect()
        transaction = connection.begin()

        # 2.创建一个临时数据库会话
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        _db.session = session

        # 3.抛出数据库实例
        yield _db

        # 4.回退数据库并关闭连接，随后清除会话
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def app_context(app):
    """提供应用上下文"""
    with app.app_context():
        yield app


# 标记定义
def pytest_configure(config):
    """配置 pytest 标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "agent: Agent 相关测试"
    )
