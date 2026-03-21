#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化测试账号脚本
用法: python init_test_account.py
"""
import os
import sys
import base64
import secrets
import dotenv

# 加载环境变量
dotenv.load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.http.app import app
from internal.model import Account
from internal.extension.database_extension import db
from pkg.password import hash_password


def init_test_account():
    """初始化测试账号"""
    with app.app_context():
        # 1. 检查测试账号是否已存在
        test_email = os.getenv("TEST_EMAIL", "test@imooc.com")
        test_password = os.getenv("TEST_PASSWORD", "Test1234")
        
        existing_account = db.session.query(Account).filter(
            Account.email == test_email
        ).one_or_none()
        
        if existing_account:
            print(f"✓ 测试账号已存在: {test_email}")
            return
        
        # 2. 生成密码盐值和加密密码
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()
        password_hashed = hash_password(test_password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()
        
        # 3. 创建测试账号
        account = Account(
            name="Test User",
            email=test_email,
            avatar="",
            password=base64_password_hashed,
            password_salt=base64_salt,
        )
        
        db.session.add(account)
        db.session.commit()
        
        print(f"✓ 测试账号创建成功!")
        print(f"  邮箱: {test_email}")
        print(f"  密码: {test_password}")


if __name__ == "__main__":
    try:
        init_test_account()
    except Exception as e:
        print(f"✗ 创建测试账号失败: {e}")
        sys.exit(1)
