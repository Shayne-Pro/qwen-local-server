#!/usr/bin/env python3
"""Quick test script for Qwen3.5-27B GGUF API service with streaming support"""

from openai import OpenAI
import sys
import time

def test_qwen_27b_gguf():
    """Test the Qwen3.5-27B GGUF API service with streaming output"""

    client = OpenAI(
        base_url="http://localhost:8001/v1",
        api_key="dummy",
        timeout=120.0
    )

    print("Testing Qwen3.5-27B GGUF API Service (Streaming)")
    print("=" * 60)

    try:
        # 测试提示
        test_prompt = "你好，请用一句话介绍你自己。"

        print(f"\n用户: {test_prompt}")
        print("模型: ", end="", flush=True)

        # 开始计时
        start_time = time.time()

        # 创建流式请求
        stream = client.chat.completions.create(
            model="qwen",
            messages=[
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=1024,
            temperature=0.7,
            stream=True
        )

        # 处理流式响应
        full_content = []
        token_count = 0
        first_token_time = None

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                # 记录首token时间
                if first_token_time is None:
                    first_token_time = time.time()

                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_content.append(content)
                token_count += 1

        # 计算统计信息
        end_time = time.time()
        total_time = end_time - start_time
        first_token_latency = first_token_time - start_time if first_token_time else 0
        generation_time = end_time - first_token_time if first_token_time else 0
        tokens_per_second = token_count / generation_time if generation_time > 0 else 0

        print("\n")
        print("=" * 60)
        print("✓ API 调用成功!")
        print(f"📊 统计信息:")
        print(f"  - 生成tokens: {token_count}")
        print(f"  - 总耗时: {total_time:.2f}秒")
        print(f"  - 首token延迟: {first_token_latency:.2f}秒")
        print(f"  - 生成速度: {tokens_per_second:.1f} tokens/s")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_qwen_27b_gguf()
