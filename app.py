#!/usr/bin/env python3
"""Chainlit web chat interface for Qwopus3.5-27B / Qwen3.5-27B models"""

import re
import time

import chainlit as cl
from openai import OpenAI

API_BASE = "http://localhost:8001/v1"
API_KEY = "dummy"
MODEL_NAME = "qwen"
DEFAULT_MAX_TOKENS = 2048


def get_messages_from_context() -> list[dict]:
    """Convert Chainlit chat context to OpenAI message format."""
    messages = []
    for msg in cl.chat_context.get():
        role = "user" if msg.type == "user_message" else "assistant"
        if msg.content:
            messages.append({"role": role, "content": msg.content})
    return messages


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("client", OpenAI(base_url=API_BASE, api_key=API_KEY, timeout=120.0))
    await cl.Message(content="你好！我是 Qwopus3.5-27B 智能助手，有什么可以帮你的？").send()


@cl.on_message
async def on_message(message: cl.Message):
    client: OpenAI = cl.user_session.get("client")
    messages = get_messages_from_context()

    start_time = time.time()
    first_token_time = None
    token_count = 0

    in_think = False
    buffer = ""
    think_step: cl.Step | None = None
    answer_msg = cl.Message(content="")

    think_open_re = re.compile(r"<think\s*>")
    think_close_re = re.compile(r"</think\s*>")

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=0.7,
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices or not chunk.choices[0].delta.content:
                continue
            text = chunk.choices[0].delta.content

            if first_token_time is None:
                first_token_time = time.time()
            token_count += 1

            if in_think:
                buffer += text
                close_match = think_close_re.search(buffer)
                if close_match:
                    think_content = buffer[: close_match.start()]
                    if think_step is not None:
                        await think_step.stream_token(think_content)
                        await think_step.update()
                    after = buffer[close_match.end() :]
                    in_think = False
                    buffer = ""
                    if after.strip():
                        await answer_msg.stream_token(after)
                continue

            open_match = think_open_re.search(text)
            if open_match:
                before = text[: open_match.start()]
                if before:
                    await answer_msg.stream_token(before)
                after_tag = text[open_match.end() :]
                if after_tag.strip():
                    buffer = after_tag
                    close_in_buf = think_close_re.search(buffer)
                    if close_in_buf:
                        in_think = False
                        await answer_msg.stream_token(buffer[close_in_buf.end() :])
                        buffer = ""
                    else:
                        in_think = True
                        think_step = cl.Step(name="思考过程", type="thinking")
                        think_step.streaming = True
                        await think_step.send()
                else:
                    in_think = True
                    buffer = ""
                    think_step = cl.Step(name="思考过程", type="thinking")
                    think_step.streaming = True
                    await think_step.send()
                continue

            await answer_msg.stream_token(text)

        if in_think and think_step is not None:
            if buffer:
                await think_step.stream_token(buffer)
            await think_step.update()

        await answer_msg.send()

        total_time = time.time() - start_time
        first_token_latency = first_token_time - start_time if first_token_time else 0
        generation_time = time.time() - first_token_time if first_token_time else 0
        tokens_per_second = token_count / generation_time if generation_time > 0 else 0

        stats = (
            f"📊 生成 {token_count} tokens | "
            f"首 token 延迟 {first_token_latency:.2f}s | "
            f"生成速度 {tokens_per_second:.1f} tokens/s"
        )
        await cl.Message(content=stats).send()

    except Exception as e:
        error_msg = f"✗ 调用失败: {e}"
        if answer_msg.content:
            await answer_msg.send()
        await cl.Message(content=error_msg).send()
