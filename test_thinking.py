#!/usr/bin/env python3
"""测试 Qwen3.6-27B 模型是否具有思考（thinking）能力"""

import re
import sys
import time

from openai import OpenAI


def parse_thinking_and_answer(full_text):
    """从响应中分离思考内容和正式回答"""
    think_end = '</think'
    idx = full_text.find(think_end)
    if idx >= 0:
        thinking = full_text[:idx].strip()
        if thinking.startswith('<think'):
            thinking = thinking[len('<think'):].lstrip('>').lstrip('\n')
        answer = full_text[idx + len(think_end):].strip().lstrip('>').lstrip('\n')
        return thinking, answer
    return None, full_text.strip()


def stream_test(client, prompt, max_tokens=2048, temperature=0.7):
    """发送流式请求，收集完整响应并分析思考内容"""
    start_time = time.time()
    stream = client.chat.completions.create(
        model="qwen",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )

    full_content = []
    token_count = 0
    first_token_time = None

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = time.time()
            content = chunk.choices[0].delta.content
            full_content.append(content)
            token_count += 1

    end_time = time.time()
    full_text = "".join(full_content)
    thinking, answer = parse_thinking_and_answer(full_text)

    total_time = end_time - start_time
    first_token_latency = (first_token_time - start_time) if first_token_time else 0
    gen_time = (end_time - first_token_time) if first_token_time else 0
    tokens_per_sec = token_count / gen_time if gen_time > 0 else 0

    return {
        "full_text": full_text,
        "thinking": thinking,
        "answer": answer,
        "has_thinking": thinking is not None and len(thinking) > 0,
        "token_count": token_count,
        "total_time": total_time,
        "first_token_latency": first_token_latency,
        "tokens_per_second": tokens_per_sec,
    }


def print_result(title, result):
    """打印单个测试场景的结果"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

    if result["has_thinking"]:
        print(f"  是否思考: 是 ✓")
        think_preview = result["thinking"][:300]
        if len(result["thinking"]) > 300:
            think_preview += "..."
        print(f"  思考长度: {len(result['thinking'])} 字符")
        print(f"  思考内容预览:")
        for line in think_preview.split("\n")[:10]:
            print(f"    {line}")
        print(f"\n  正式回答:")
        for line in result["answer"].split("\n")[:20]:
            print(f"    {line}")
    else:
        print(f"  是否思考: 否 ✗")
        print(f"  回答内容:")
        for line in result["answer"].split("\n")[:20]:
            print(f"    {line}")

    print(f"\n  📊 统计:")
    print(f"    - 总 tokens: {result['token_count']}")
    print(f"    - 总耗时: {result['total_time']:.2f}s")
    print(f"    - 首 token 延迟: {result['first_token_latency']:.2f}s")
    print(f"    - 速度: {result['tokens_per_second']:.1f} tokens/s")


def main():
    client = OpenAI(
        base_url="http://localhost:8001/v1",
        api_key="dummy",
        timeout=300.0,
    )

    scenarios = [
        {
            "title": "场景1: 简单问候（可能不触发思考）",
            "prompt": "你好，请用一句话介绍你自己。",
            "max_tokens": 1024,
            "temperature": 0.7,
        },
        {
            "title": "场景2: 数学推理（应触发思考）",
            "prompt": "一个水池有两个水管，A管单独注满需要6小时，B管单独注满需要4小时。两管同时打开，几小时能注满？请给出详细解题过程。",
            "max_tokens": 4096,
            "temperature": 0.3,
        },
        {
            "title": "场景3: 代码逻辑推理（应触发思考）",
            "prompt": "写一个Python函数，判断一个整数是否是回文数。要求：不能将整数转为字符串，只能用数学方法。包含详细注释和测试用例。",
            "max_tokens": 4096,
            "temperature": 0.3,
        },
    ]

    print("=" * 60)
    print("  Qwen3.6-27B 思考能力测试")
    print("=" * 60)

    results = []
    for s in scenarios:
        print(f"\n⏳ 正在测试: {s['title']}...")
        r = stream_test(client, s["prompt"], s["max_tokens"], s["temperature"])
        results.append((s["title"], r))
        print_result(s["title"], r)

    # 总结
    think_count = sum(1 for _, r in results if r["has_thinking"])
    total_tokens = sum(r["token_count"] for _, r in results)
    total_time = sum(r["total_time"] for _, r in results)

    print(f"\n{'=' * 60}")
    print(f"  总结")
    print(f"{'=' * 60}")
    print(f"  测试场景数: {len(results)}")
    print(f"  触发思考次数: {think_count}/{len(results)}")
    print(f"  总 tokens: {total_tokens}")
    print(f"  总耗时: {total_time:.2f}s")
    print(f"  平均速度: {total_tokens / total_time:.1f} tokens/s")

    if think_count == len(results):
        print(f"\n  结论: ✓ 该模型在所有场景中都会进行思考")
    elif think_count > 0:
        print(f"\n  结论: ~ 该模型在部分场景中会进行思考（{think_count}/{len(results)}）")
    else:
        print(f"\n  结论: ✗ 该模型没有思考能力")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
