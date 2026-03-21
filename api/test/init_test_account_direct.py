#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化测试账号脚本 - 直接数据库操作版本
用法: python init_test_account_direct.py
"""
import os
import base64
import secrets
import hashlib
import binascii
import dotenv
from datetime import datetime

# 加载环境变量
dotenv.load_dotenv()

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("需要安装 psycopg2: pip install psycopg2-binary")
    exit(1)


def hash_password(password: str, salt: bytes) -> bytes:
    """将传入的密码+盐值进行哈希加密"""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 10000)
    return binascii.hexlify(dk)


def init_test_account():
    """初始化测试账号"""
    # 1. 获取数据库连接信息
    db_uri = os.getenv("SQLALCHEMY_DATABASE_URI", "postgresql://chyang:@localhost:5432/llmops?client_encoding=utf8")
    test_email = os.getenv("TEST_EMAIL", "test@imooc.com")
    test_password = os.getenv("TEST_PASSWORD", "Test1234")
    
    # 2. 解析数据库连接字符串
    # postgresql://user:password@host:port/database
    try:
        parts = db_uri.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        host_port = parts[1].split("/")
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_port[0].split(":")[0]
        port = int(host_port[0].split(":")[1]) if ":" in host_port[0] else 5432
        database = host_port[1].split("?")[0]
        
        print(f"连接数据库: {user}@{host}:{port}/{database}")
        
        # 3. 连接数据库
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # 4. 检查测试账号是否已存在
        cursor.execute("SELECT id FROM account WHERE email = %s", (test_email,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"✓ 测试账号已存在: {test_email}")
            cursor.close()
            conn.close()
            return
        
        # 5. 生成密码盐值和加密密码
        salt = secrets.token_bytes(16)
        base64_salt = base64.b64encode(salt).decode()
        password_hashed = hash_password(test_password, salt)
        base64_password_hashed = base64.b64encode(password_hashed).decode()
        
        # 6. 插入测试账号
        now = datetime.now()
        cursor.execute("""
            INSERT INTO account (name, email, avatar, password, password_salt, last_login_at, last_login_ip, updated_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            "Test User",
            test_email,
            "",
            base64_password_hashed,
            base64_salt,
            now,
            "127.0.0.1",
            now,
            now
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ 测试账号创建成功!")
        print(f"  邮箱: {test_email}")
        print(f"  密码: {test_password}")
        
    except Exception as e:
        print(f"✗ 创建测试账号失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    init_test_account()
