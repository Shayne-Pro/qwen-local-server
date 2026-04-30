#!/usr/bin/env python3
"""通用聊天测试脚本 - 测试 Qwen 模型
用法:
  python test_chat.py                          # 快速测试 (greeting)
  python test_chat.py --full                   # 完整 3 场景测试
  python test_chat.py --preset thinking_coding # 指定预设
"""

import sys
import time

from openai import OpenAI

from presets import get_preset, preset_to_api_params, adapt_extra_body, get_chat_template_kwargs

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="dummy",
    timeout=120.0,
)


def print_section(title):
    print(f"\n{title}")
    print("-" * 60)


def stream_response(messages, max_tokens=1024, preset_name=None):
    p = get_preset(preset_name)
    api_params, extra_body = preset_to_api_params(p)
    extra_body = adapt_extra_body(extra_body)
    template_kwargs = get_chat_template_kwargs(p)
    extra_body["chat_template_kwargs"] = template_kwargs

    print(f"模型 (预设: {p['description']}): ", end="", flush=True)

    start_time = time.time()
    stream = client.chat.completions.create(
        model="qwen",
        messages=messages,
        max_tokens=max_tokens,
        stream=True,
        **api_params,
        extra_body=extra_body,
    )

    full_content = []
    reasoning_parts = []
    token_count = 0
    first_token_time = None

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        rc = getattr(delta, "reasoning_content", None)
        content = delta.content

        if rc:
            reasoning_parts.append(rc)
            if first_token_time is None:
                first_token_time = time.time()
            token_count += 1

        if content:
            full_content.append(content)
            if first_token_time is None:
                first_token_time = time.time()
            token_count += 1
            print(content, end="", flush=True)

    end_time = time.time()
    total_time = end_time - start_time
    first_token_latency = (first_token_time - start_time) if first_token_time else 0
    gen_time = (end_time - first_token_time) if first_token_time else 0
    tokens_per_sec = token_count / gen_time if gen_time > 0 else 0

    think_len = sum(len(p) for p in reasoning_parts)

    print("\n")
    return {
        "content": "".join(full_content),
        "token_count": token_count,
        "total_time": total_time,
        "first_token_latency": first_token_latency,
        "tokens_per_second": tokens_per_sec,
        "thinking_chars": think_len,
    }


def quick_test(model_name, preset_name):
    print(f"\n{'=' * 60}")
    print(f"  {model_name} 快速测试 (Streaming)")
    print(f"{'=' * 60}")

    prompt = "你好，请用一句话介绍你自己。"
    print(f"\n用户: {prompt}")

    r = stream_response([{"role": "user", "content": prompt}], preset_name=preset_name)

    print(f"📊 统计:")
    print(f"  - 生成tokens: {r['token_count']}")
    if r.get("thinking_chars"):
        print(f"  - 思考内容: {r['thinking_chars']} 字符")
    print(f"  - 首token延迟: {r['first_token_latency']:.2f}秒")
    print(f"  - 生成速度: {r['tokens_per_second']:.1f} tokens/s")
    print(f"{'=' * 60}")


def full_test(model_name, preset_name):
    print(f"\n{'=' * 60}")
    print(f"  {model_name} 完整测试 (流式输出)")
    print(f"{'=' * 60}")

    results = []

    print_section("测试1: 简单问候 (max_tokens=1024)")
    print("用户: 你好，请用一句话介绍你自己。")
    r1 = stream_response(
        [{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
        max_tokens=1024, preset_name=preset_name,
    )
    print(f"📊 统计:")
    print(f"  - 生成tokens: {r1['token_count']}/1024")
    if r1.get("thinking_chars"):
        print(f"  - 思考内容: {r1['thinking_chars']} 字符")
    print(f"  - 首token延迟: {r1['first_token_latency']:.2f}秒")
    print(f"  - 生成速度: {r1['tokens_per_second']:.1f} tokens/s")
    results.append(r1)

    print_section("测试2: Python代码生成 (max_tokens=4096)")
    print("用户: 写一个Python函数计算斐波那契数列的第n项")
    r2 = stream_response(
        [{"role": "user", "content": "写一个Python函数计算斐波那契数列的第n项，包含详细注释和使用示例。"}],
        max_tokens=4096, preset_name="thinking_coding",
    )
    print(f"📊 统计:")
    print(f"  - 生成tokens: {r2['token_count']}/4096")
    if r2.get("thinking_chars"):
        print(f"  - 思考内容: {r2['thinking_chars']} 字符")
    print(f"  - 首token延迟: {r2['first_token_latency']:.2f}秒")
    print(f"  - 生成速度: {r2['tokens_per_second']:.1f} tokens/s")
    results.append(r2)

    print_section("测试3: 长文本生成 (max_tokens=2048)")
    print("用户: 请用3-5句话详细介绍量子计算的基本原理")
    r3 = stream_response(
        [{"role": "user", "content": "请用3-5句话详细介绍量子计算的基本原理，包括量子比特、叠加态和纠缠态。"}],
        max_tokens=2048, preset_name=preset_name,
    )
    print(f"📊 统计:")
    print(f"  - 生成tokens: {r3['token_count']}/2048")
    if r3.get("thinking_chars"):
        print(f"  - 思考内容: {r3['thinking_chars']} 字符")
    print(f"  - 首token延迟: {r3['first_token_latency']:.2f}秒")
    print(f"  - 生成速度: {r3['tokens_per_second']:.1f} tokens/s")
    results.append(r3)

    total_tokens = sum(r["token_count"] for r in results)
    total_time = sum(r["total_time"] for r in results)
    avg_speed = total_tokens / total_time if total_time > 0 else 0

    print(f"\n{'=' * 60}")
    print("✓ 所有测试完成！服务运行正常。")
    print(f"📈 总体统计:")
    print(f"  - 总生成tokens: {total_tokens}")
    print(f"  - 总耗时: {total_time:.2f}秒")
    print(f"  - 平均速度: {avg_speed:.1f} tokens/s")
    print(f"{'=' * 60}")


def parse_args():
    args = sys.argv[1:]
    preset_name = None
    for i, arg in enumerate(args):
        if arg == "--preset" and i + 1 < len(args):
            preset_name = args[i + 1]
    return preset_name


def main():
    preset_name = parse_args()

    try:
        client.models.list()
        model_name = "Qwen"
    except Exception as e:
        print(f"✗ 无法连接到 API 服务: {e}")
        sys.exit(1)

    if "--full" in sys.argv:
        full_test(model_name, preset_name)
    else:
        quick_test(model_name, preset_name)


if __name__ == "__main__":
    main()
