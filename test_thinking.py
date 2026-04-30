#!/usr/bin/env python3
"""测试模型思考（thinking）能力 - 使用 reasoning_content 分离模式

用法:
  python test_thinking.py                          # 默认 thinking_coding 预设
  python test_thinking.py --preset thinking_general
"""

import sys
import time

from openai import OpenAI

from presets import get_preset, preset_to_api_params, adapt_extra_body, get_chat_template_kwargs

DEFAULT_THINKING_PRESET = "thinking_coding"


def stream_test(client, prompt, max_tokens=2048, preset_name=None):
    p = get_preset(preset_name or DEFAULT_THINKING_PRESET)
    api_params, extra_body = preset_to_api_params(p)
    extra_body = adapt_extra_body(extra_body)
    template_kwargs = get_chat_template_kwargs(p)
    extra_body["chat_template_kwargs"] = template_kwargs

    start_time = time.time()
    stream = client.chat.completions.create(
        model="qwen",
        messages=[{"role": "user", "content": prompt}],
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

    end_time = time.time()
    thinking_text = "".join(reasoning_parts).strip()
    answer_text = "".join(full_content).strip()

    total_time = end_time - start_time
    first_token_latency = (first_token_time - start_time) if first_token_time else 0
    gen_time = (end_time - first_token_time) if first_token_time else 0
    tokens_per_sec = token_count / gen_time if gen_time > 0 else 0

    return {
        "thinking": thinking_text,
        "answer": answer_text,
        "has_thinking": len(thinking_text) > 0,
        "token_count": token_count,
        "total_time": total_time,
        "first_token_latency": first_token_latency,
        "tokens_per_second": tokens_per_sec,
    }


def print_result(title, result):
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


def parse_args():
    args = sys.argv[1:]
    preset_name = None
    for i, arg in enumerate(args):
        if arg == "--preset" and i + 1 < len(args):
            preset_name = args[i + 1]
    return preset_name


def main():
    preset_name = parse_args()
    p = get_preset(preset_name or DEFAULT_THINKING_PRESET)

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
        },
        {
            "title": "场景2: 数学推理（应触发思考）",
            "prompt": "一个水池有两个水管，A管单独注满需要6小时，B管单独注满需要4小时。两管同时打开，几小时能注满？请给出详细解题过程。",
            "max_tokens": 4096,
        },
        {
            "title": "场景3: 代码逻辑推理（应触发思考）",
            "prompt": "写一个Python函数，判断一个整数是否是回文数。要求：不能将整数转为字符串，只能用数学方法。包含详细注释和测试用例。",
            "max_tokens": 4096,
        },
    ]

    print("=" * 60)
    print(f"  模型思考能力测试 (reasoning_content 分离模式)")
    print(f"  预设: {p['description']}")
    print("=" * 60)

    results = []
    for s in scenarios:
        print(f"\n⏳ 正在测试: {s['title']}...")
        r = stream_test(client, s["prompt"], s["max_tokens"], preset_name)
        results.append((s["title"], r))
        print_result(s["title"], r)

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
