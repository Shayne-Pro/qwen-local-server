#!/usr/bin/env python3
"""完整测试 Qwen3.5-27B GGUF API 服务 - 流式输出版本"""

from openai import OpenAI
import time

def print_section(title):
    """打印测试章节标题"""
    print(f"\n{title}")
    print("-" * 60)

def stream_response(client, messages, max_tokens=1024, temperature=0.7):
    """处理流式响应并显示统计信息"""
    print("模型: ", end="", flush=True)

    start_time = time.time()
    stream = client.chat.completions.create(
        model="qwen",
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True
    )

    full_content = []
    token_count = 0
    first_token_time = None

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = time.time()

            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_content.append(content)
            token_count += 1

    end_time = time.time()
    total_time = end_time - start_time
    first_token_latency = first_token_time - start_time if first_token_time else 0
    generation_time = end_time - first_token_time if first_token_time else 0
    tokens_per_second = token_count / generation_time if generation_time > 0 else 0

    print("\n")

    return {
        "content": "".join(full_content),
        "token_count": token_count,
        "total_time": total_time,
        "first_token_latency": first_token_latency,
        "tokens_per_second": tokens_per_second
    }

def test_qwen_27b_full():
    """完整测试 Qwen3.5-27B GGUF API 服务 - 流式输出"""

    client = OpenAI(
        base_url="http://localhost:8001/v1",
        api_key="dummy",
        timeout=120.0
    )

    print("Qwen3.5-27B GGUF API 服务完整测试 (流式输出)")
    print("=" * 60)

    # 测试1: 简单问候
    print_section("测试1: 简单问候 (max_tokens=1024)")
    print("用户: 你好，请用一句话介绍你自己。")

    result1 = stream_response(
        client,
        messages=[{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
        max_tokens=1024,
        temperature=0.7
    )

    print(f"📊 统计:")
    print(f"  - 生成tokens: {result1['token_count']}/1024")
    print(f"  - 首token延迟: {result1['first_token_latency']:.2f}秒")
    print(f"  - 生成速度: {result1['tokens_per_second']:.1f} tokens/s")

    # 测试2: 代码生成
    print_section("测试2: Python代码生成 (max_tokens=4096)")
    print("用户: 写一个Python函数计算斐波那契数列的第n项")

    result2 = stream_response(
        client,
        messages=[{"role": "user", "content": "写一个Python函数计算斐波那契数列的第n项，包含详细注释和使用示例。"}],
        max_tokens=4096,
        temperature=0.3
    )

    print(f"📊 统计:")
    print(f"  - 生成tokens: {result2['token_count']}/4096")
    print(f"  - 首token延迟: {result2['first_token_latency']:.2f}秒")
    print(f"  - 生成速度: {result2['tokens_per_second']:.1f} tokens/s")

    # 测试3: 流式输出 - 长文本生成
    print_section("测试3: 长文本生成 (max_tokens=2048)")
    print("用户: 请用3-5句话详细介绍量子计算的基本原理")

    result3 = stream_response(
        client,
        messages=[{"role": "user", "content": "请用3-5句话详细介绍量子计算的基本原理，包括量子比特、叠加态和纠缠态。"}],
        max_tokens=2048,
        temperature=0.7
    )

    print(f"📊 统计:")
    print(f"  - 生成tokens: {result3['token_count']}/2048")
    print(f"  - 首token延迟: {result3['first_token_latency']:.2f}秒")
    print(f"  - 生成速度: {result3['tokens_per_second']:.1f} tokens/s")

    # 总结
    total_tokens = result1['token_count'] + result2['token_count'] + result3['token_count']
    total_time = result1['total_time'] + result2['total_time'] + result3['total_time']
    avg_speed = total_tokens / total_time if total_time > 0 else 0

    print("\n" + "=" * 60)
    print("✓ 所有测试完成！服务运行正常。")
    print(f"📈 总体统计:")
    print(f"  - 总生成tokens: {total_tokens}")
    print(f"  - 总耗时: {total_time:.2f}秒")
    print(f"  - 平均速度: {avg_speed:.1f} tokens/s")
    print("=" * 60)

if __name__ == "__main__":
    test_qwen_27b_full()
