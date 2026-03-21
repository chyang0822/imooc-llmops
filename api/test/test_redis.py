#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/03/21
@Author  : test
@File    : test_redis.py

Redis 连通性测试
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_redis_connection():
    """测试 Redis 连接"""
    try:
        from redis import Redis
        
        # 创建 Redis 客户端
        redis_client = Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # 测试连接
        result = redis_client.ping()
        
        if result:
            print("✅ Redis 连接成功！")
            print(f"   Host: localhost")
            print(f"   Port: 6379")
            print(f"   DB: 0")
            return True
        else:
            print("❌ Redis 连接失败：ping 返回 False")
            return False
            
    except ConnectionRefusedError:
        print("❌ Redis 连接失败：连接被拒绝")
        print("   请确保 Redis 已启动: brew services start redis")
        return False
    except Exception as e:
        print(f"❌ Redis 连接失败：{str(e)}")
        return False


def test_redis_operations():
    """测试 Redis 基本操作"""
    try:
        from redis import Redis
        
        redis_client = Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # 测试 SET 操作
        redis_client.set('test_key', 'test_value')
        print("✅ SET 操作成功")
        
        # 测试 GET 操作
        value = redis_client.get('test_key')
        if value == 'test_value':
            print("✅ GET 操作成功")
        else:
            print(f"❌ GET 操作失败：期望 'test_value'，得到 '{value}'")
            return False
        
        # 测试 DEL 操作
        redis_client.delete('test_key')
        value = redis_client.get('test_key')
        if value is None:
            print("✅ DEL 操作成功")
        else:
            print(f"❌ DEL 操作失败：期望 None，得到 '{value}'")
            return False
        
        # 测试 SETEX 操作
        redis_client.setex('expire_key', 10, 'expire_value')
        value = redis_client.get('expire_key')
        if value == 'expire_value':
            print("✅ SETEX 操作成功")
        else:
            print(f"❌ SETEX 操作失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Redis 操作失败：{str(e)}")
        return False


def main():
    """主函数"""
    print("╔════════════════════════════════════════════════════════════╗")
    print("║              Redis 连通性测试                              ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # 测试连接
    print("1️⃣  测试 Redis 连接...")
    connection_ok = test_redis_connection()
    print()
    
    if not connection_ok:
        print("❌ Redis 连接失败，请先启动 Redis")
        print("\n启动 Redis 的方法:")
        print("  brew services start redis")
        print("\n或者:")
        print("  redis-server")
        return False
    
    # 测试基本操作
    print("2️⃣  测试 Redis 基本操作...")
    operations_ok = test_redis_operations()
    print()
    
    if operations_ok:
        print("✅ Redis 连通性测试通过！")
        print("\n现在可以运行 AgentQueueManager 单元测试了")
        return True
    else:
        print("❌ Redis 操作测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
