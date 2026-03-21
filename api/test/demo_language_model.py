#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语言模型 Demo 测试脚本
分别测试 providers.yaml 中定义的所有模型：
  - OpenAI      : gpt-4o-mini
  - Moonshot    : moonshot-v1-8k
  - 通义千问     : qwen-max
  - Ollama      : qwen2.5-7b  (本地服务，需提前启动)
  - DeepSeek    : deepseek-chat

运行方式（在 api/ 目录下）：
    python test/demo_language_model.py

说明：
  - 请先复制 .env.example 为 .env 并填写各服务商的 API KEY。
  - 不想测试的模型可将对应的 ENABLED 改为 False。
  - Ollama 需要本地已启动并拉取 qwen2.5:7b 模型。
"""
import os
import sys

# 将 api/ 目录加入路径，确保能正确 import 项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载 api/.env 文件
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# ──────────────────────────────────────────
# 各模型开关（不想测试的改为 False）
# ──────────────────────────────────────────
ENABLED = {
    "openai": True,
    "moonshot": True,
    "tongyi": True,
    "ollama": True,
    "deepseek": True,
}

TEST_PROMPT = "用一句话介绍你自己，并说明你是哪个公司的模型。"


# ──────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────
def separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def invoke_model(label: str, model_instance, prompt: str):
    """调用模型并打印结果，捕获异常避免单个模型失败中断整体测试"""
    separator(label)
    print(f"[Prompt] {prompt}")
    try:
        from langchain_core.messages import HumanMessage
        response = model_instance.invoke([HumanMessage(content=prompt)])
        # ChatModel 返回 AIMessage，CompletionModel 返回字符串
        content = response.content if hasattr(response, "content") else str(response)
        print(f"[Response] {content}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")


# ──────────────────────────────────────────
# 1. OpenAI — gpt-4o-mini
# ──────────────────────────────────────────
def test_openai():
    from internal.core.language_model.providers.openai.chat import Chat
    model = Chat(
        model="gpt-3.5-turbo-16k",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_api_base=os.getenv("OPENAI_API_BASE") or None,
        temperature=0.7,
        max_tokens=512,
    )
    invoke_model("OpenAI · gpt-3.5-turbo-16k", model, TEST_PROMPT)


# ──────────────────────────────────────────
# 2. Moonshot — moonshot-v1-8k
# ──────────────────────────────────────────
# def test_moonshot():
#     from internal.core.language_model.providers.moonshot.chat import Chat
#     model = Chat(
#         model="moonshot-v1-8k",
#         moonshot_api_key=os.getenv("MOONSHOT_API_KEY"),
#         temperature=0.7,
#         max_tokens=512,
#     )
#     invoke_model("Moonshot · moonshot-v1-8k", model, TEST_PROMPT)


# # ──────────────────────────────────────────
# # 3. 通义千问 — qwen-max
# # ──────────────────────────────────────────
# def test_tongyi():
#     from internal.core.language_model.providers.tongyi.chat import Chat
#     model = Chat(
#         model="qwen-max",
#         dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
#         temperature=0.7,
#         max_tokens=512,
#     )
#     invoke_model("通义千问 · qwen-max", model, TEST_PROMPT)


# # ──────────────────────────────────────────
# # 4. Ollama — qwen2.5:7b（本地）
# # ──────────────────────────────────────────
# def test_ollama():
#     from internal.core.language_model.providers.ollama.chat import Chat
#     model = Chat(
#         model="qwen2.5:7b",
#         base_url=os.getenv("OLLAMA_API_BASE", "http://localhost:11434"),
#         temperature=0.7,
#         num_predict=512,  # Ollama 使用 num_predict 控制最大输出长度
#     )
#     invoke_model("Ollama · qwen2.5:7b（本地）", model, TEST_PROMPT)


# # ──────────────────────────────────────────
# # 5. DeepSeek — deepseek-chat
# # ──────────────────────────────────────────
# def test_deepseek():
#     from internal.core.language_model.providers.deepseek.chat import Chat
#     model = Chat(
#         model="deepseek-chat",
#         # api_key / api_base 已在 Chat.__init__ 中从环境变量读取
#         temperature=0.7,
#         max_tokens=512,
#     )
#     invoke_model("DeepSeek · deepseek-chat", model, TEST_PROMPT)


# ──────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  LLMOps 语言模型 Demo 测试")
    print("#" * 60)
    print(f"[测试问题] {TEST_PROMPT}")

    if ENABLED["openai"]:
        test_openai()

    # if ENABLED["moonshot"]:
    #     test_moonshot()

    # if ENABLED["tongyi"]:
    #     test_tongyi()

    # if ENABLED["ollama"]:
    #     test_ollama()

    # if ENABLED["deepseek"]:
    #     test_deepseek()

    print("\n" + "#" * 60)
    print("#  全部测试完成")
    print("#" * 60 + "\n")