#!/usr/bin/env python3
"""Chainlit web chat interface for local LLM API service."""

import chainlit as cl
from openai import OpenAI

from presets import get_preset, preset_to_api_params, list_presets

THINK_TAG = "</think"

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="dummy",
    timeout=300.0,
)

current_preset = get_preset()
api_params, extra_body_params = preset_to_api_params(current_preset)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("messages", [])
    await cl.Message(
        content=f"你好！我是本地 LLM 助手，有什么可以帮你的？\n\n"
        f"📊 当前预设：**{current_preset['description']}**"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})

    msg = cl.Message(content="")
    await msg.send()

    try:
        stream = client.chat.completions.create(
            model="qwen",
            messages=messages,
            max_tokens=16384,
            stream=True,
            **api_params,
            extra_body={
                **extra_body_params,
            },
        )

        full_content = []
        thinking_step = None
        buffer = ""
        in_thinking = True

        for chunk in stream:
            if not chunk.choices or not chunk.choices[0].delta.content:
                continue
            content = chunk.choices[0].delta.content
            full_content.append(content)

            if in_thinking:
                buffer += content
                tag_pos = buffer.find(THINK_TAG)
                if tag_pos >= 0:
                    in_thinking = False
                    tail = buffer[tag_pos + len(THINK_TAG):].lstrip(">").lstrip("\n")
                    if thinking_step:
                        await thinking_step.stream_token(buffer[:tag_pos].rstrip())
                        await thinking_step.send()
                    if tail:
                        await msg.stream_token(tail)
                    buffer = ""
                else:
                    flush_pos = max(0, len(buffer) - len(THINK_TAG))
                    safe_part = buffer[:flush_pos]
                    if safe_part:
                        if thinking_step is None:
                            thinking_step = cl.Step(
                                name="💭 思考过程",
                                type="run",
                                auto_collapse=True,
                                default_open=False,
                            )
                            await thinking_step.send()
                            if safe_part.startswith("<think"):
                                safe_part = safe_part[len("<think"):].lstrip(">").lstrip("\n")
                        if safe_part:
                            await thinking_step.stream_token(safe_part)
                    buffer = buffer[flush_pos:]
                continue

            await msg.stream_token(content)

        if in_thinking and buffer:
            if thinking_step is None:
                thinking_step = cl.Step(
                    name="💭 思考过程",
                    type="run",
                    auto_collapse=True,
                    default_open=False,
                )
                await thinking_step.send()
                if buffer.startswith("<think"):
                    buffer = buffer[len("<think"):].lstrip(">").lstrip("\n")
            await thinking_step.stream_token(buffer)
            await thinking_step.send()

        await msg.update()
        messages.append({"role": "assistant", "content": "".join(full_content)})

    except Exception as e:
        await msg.update()
        await cl.Message(content=f"⚠ 请求失败: {e}").send()
        import traceback
        traceback.print_exc()
