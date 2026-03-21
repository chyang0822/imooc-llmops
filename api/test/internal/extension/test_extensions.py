#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    : test_extensions.py
单元测试：internal/extension 下各扩展的初始化逻辑

测试覆盖：
  - redis_extension  : init_app 连接池配置、SSL 分支、app.extensions 注册
  - celery_extension : init_app FlaskTask 上下文包装、app.extensions 注册
  - logging_extension: init_app 日志级别、handler 数量、文件夹创建

运行方式（在 api/ 目录下）：
    pytest test/internal/extension/test_extensions.py --noconftest -p no:langsmith -v
"""
import logging
import os
import tempfile
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from flask import Flask


# ─────────────────────────────────────────────────────────
# 辅助工厂
# ─────────────────────────────────────────────────────────

def _make_app(debug: bool = False, extra_config: dict = None) -> Flask:
    """创建最小 Flask 测试应用"""
    app = Flask(__name__)
    app.config.update({
        "TESTING": True,
        "DEBUG": debug,
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_USERNAME": None,
        "REDIS_PASSWORD": None,
        "REDIS_DB": 0,
        "REDIS_USE_SSL": False,
        "CELERY": {
            "broker_url": "memory://",
            "result_backend": "cache+memory://",
        },
    })
    if extra_config:
        app.config.update(extra_config)
    return app


# ─────────────────────────────────────────────────────────
# 1. redis_extension 测试
# ─────────────────────────────────────────────────────────

class TestRedisExtension:
    """测试 redis_extension.init_app"""

    def test_redis_registered_in_app_extensions(self):
        """init_app 后 redis 客户端应注册到 app.extensions"""
        from internal.extension.redis_extension import init_app, redis_client
        app = _make_app()
        with patch("redis.ConnectionPool") as mock_pool:
            init_app(app)
            assert "redis" in app.extensions
            assert app.extensions["redis"] is redis_client

    def test_redis_connection_pool_uses_app_config(self):
        """连接池参数应与 app.config 一致"""
        from internal.extension.redis_extension import init_app
        app = _make_app(extra_config={
            "REDIS_HOST": "192.168.1.100",
            "REDIS_PORT": 6380,
            "REDIS_DB": 2,
        })
        with patch("redis.ConnectionPool") as mock_pool:
            init_app(app)
            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs["host"] == "192.168.1.100"
            assert call_kwargs["port"] == 6380
            assert call_kwargs["db"] == 2

    def test_redis_non_ssl_uses_plain_connection(self):
        """非 SSL 模式应使用普通 Connection 类"""
        from internal.extension.redis_extension import init_app
        from redis.connection import Connection
        app = _make_app(extra_config={"REDIS_USE_SSL": False})
        with patch("redis.ConnectionPool") as mock_pool:
            init_app(app)
            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs["connection_class"] is Connection

    def test_redis_ssl_uses_ssl_connection(self):
        """SSL 模式应使用 SSLConnection 类"""
        from internal.extension.redis_extension import init_app
        from redis.connection import SSLConnection
        app = _make_app(extra_config={"REDIS_USE_SSL": True})
        with patch("redis.ConnectionPool") as mock_pool:
            init_app(app)
            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs["connection_class"] is SSLConnection

    def test_redis_default_host_when_not_configured(self):
        """未配置 REDIS_HOST 时应使用默认值 localhost"""
        from internal.extension.redis_extension import init_app
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["CELERY"] = {}
        with patch("redis.ConnectionPool") as mock_pool:
            init_app(app)
            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs["host"] == "localhost"
            assert call_kwargs["port"] == 6379


# ─────────────────────────────────────────────────────────
# 2. celery_extension 测试
# ─────────────────────────────────────────────────────────

class TestCeleryExtension:
    """测试 celery_extension.init_app"""

    def test_celery_registered_in_app_extensions(self):
        """init_app 后 celery 应注册到 app.extensions"""
        from internal.extension.celery_extension import init_app
        app = _make_app()
        init_app(app)
        assert "celery" in app.extensions

    def test_celery_app_name_matches_flask_app(self):
        """Celery 应用名字应与 Flask 应用名字一致"""
        from internal.extension.celery_extension import init_app
        app = _make_app()
        init_app(app)
        celery_app = app.extensions["celery"]
        assert celery_app.main == app.name

    def test_flask_task_runs_in_app_context(self):
        """FlaskTask.__call__ 应在 Flask 应用上下文中执行任务"""
        from internal.extension.celery_extension import init_app
        app = _make_app()
        init_app(app)
        celery_app = app.extensions["celery"]

        # 创建一个简单任务，记录执行时是否在 app context 内
        context_captured = []

        @celery_app.task
        def sample_task():
            from flask import current_app
            try:
                context_captured.append(current_app.name)
            except RuntimeError:
                context_captured.append(None)
            return "done"

        # 直接调用 FlaskTask.__call__（同步，不通过 broker）
        result = sample_task.apply()
        assert result.result == "done"
        assert context_captured[0] == app.name

    def test_celery_config_applied(self):
        """Celery 配置应从 app.config['CELERY'] 中加载"""
        from internal.extension.celery_extension import init_app
        app = _make_app(extra_config={
            "CELERY": {
                "broker_url": "memory://",
                "result_backend": "cache+memory://",
                "task_serializer": "json",
            }
        })
        init_app(app)
        celery_app = app.extensions["celery"]
        assert celery_app.conf.task_serializer == "json"


# ─────────────────────────────────────────────────────────
# 3. logging_extension 测试
# ─────────────────────────────────────────────────────────

class TestLoggingExtension:
    """测试 logging_extension.init_app"""

    def _clean_root_handlers(self):
        """清理 root logger 的 handler，避免测试间相互影响"""
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass

    def test_log_folder_created_if_not_exists(self):
        """日志文件夹不存在时应自动创建"""
        from internal.extension.logging_extension import init_app
        self._clean_root_handlers()
        app = _make_app(debug=False)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                init_app(app)
                log_folder = os.path.join(tmpdir, "storage", "log")
                assert os.path.exists(log_folder)
            self._clean_root_handlers()

    def test_log_level_warning_in_production(self):
        """生产模式（debug=False）下根 logger 级别应为 WARNING"""
        from internal.extension.logging_extension import init_app
        self._clean_root_handlers()
        app = _make_app(debug=False)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                with patch.dict(os.environ, {"FLASK_ENV": "production"}):
                    init_app(app)
                    assert logging.getLogger().level == logging.WARNING
            self._clean_root_handlers()

    def test_log_level_debug_in_development(self):
        """开发模式（debug=True）下根 logger 级别应为 DEBUG"""
        from internal.extension.logging_extension import init_app
        self._clean_root_handlers()
        app = _make_app(debug=True)
        app.debug = True

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                init_app(app)
                assert logging.getLogger().level == logging.DEBUG
            self._clean_root_handlers()

    def test_console_handler_added_in_debug_mode(self):
        """debug 模式下应额外添加 StreamHandler（控制台输出）"""
        from internal.extension.logging_extension import init_app
        self._clean_root_handlers()
        app = _make_app(debug=True)
        app.debug = True

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                init_app(app)
                handlers = logging.getLogger().handlers
                stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)
                                   and not hasattr(h, 'baseFilename')]
                assert len(stream_handlers) >= 1
            self._clean_root_handlers()

    def test_no_console_handler_in_production(self):
        """生产模式下不应添加 StreamHandler"""
        from internal.extension.logging_extension import init_app
        self._clean_root_handlers()
        app = _make_app(debug=False)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                with patch.dict(os.environ, {"FLASK_ENV": "production"}):
                    init_app(app)
                    handlers = logging.getLogger().handlers
                    stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)
                                       and not hasattr(h, 'baseFilename')]
                    assert len(stream_handlers) == 0
            self._clean_root_handlers()

    def test_log_formatter_contains_filename_and_lineno(self):
        """日志格式应包含文件名和行号信息"""
        from internal.extension.logging_extension import init_app
        self._clean_root_handlers()
        app = _make_app(debug=False)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with patch("os.getcwd", return_value=tmpdir):
                with patch.dict(os.environ, {"FLASK_ENV": "production"}):
                    init_app(app)
                    handlers = logging.getLogger().handlers
                    assert len(handlers) > 0
                    fmt = handlers[0].formatter._fmt
                    assert "%(filename)s" in fmt
                    assert "%(lineno)d" in fmt
            self._clean_root_handlers()