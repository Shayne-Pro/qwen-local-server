#!/usr/bin/env python3
"""Chainlit web chat interface for local LLM API service."""

import chainlit as cl
from openai import OpenAI

from presets import get_preset, preset_to_api_params, adapt_extra_body, get_chat_template_kwargs, PRESETS

PRESET_LABELS = {
    "thinking_general": "💭 思考-通用",
    "thinking_coding": "💭 思考-编程",
    "instruct_general": "💬 Instruct-通用",
    "instruct_reasoning": "💬 Instruct-推理",
}

LABEL_TO_PRESET = {v: k for k, v in PRESET_LABELS.items()}

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="dummy",
    timeout=300.0,
)


def resolve_preset_name(raw):
    return LABEL_TO_PRESET.get(raw, raw)


MAX_MESSAGES = 30


def build_preset_info(preset_name):
    p = get_preset(preset_name)
    api_params, extra_body_params = preset_to_api_params(p)
    adapted = adapt_extra_body(extra_body_params)
    adapted["chat_template_kwargs"] = get_chat_template_kwargs(p)
    return p, api_params, adapted


def truncate_messages(messages, max_messages=MAX_MESSAGES):
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages


chat_settings = cl.ChatSettings(
    inputs=[
        cl.input_widget.Select(
            id="preset",
            label="采样预设",
            items=PRESET_LABELS,
            initial_value="instruct_general",
            tooltip="切换模型的采样参数和思考模式",
        ),
    ]
)


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("current_preset", "instruct_general")
    cl.user_session.set("messages", [])

    await chat_settings.send()

    preset = get_preset("instruct_general")
    await cl.Message(
        content=f"你好！我是本地 LLM 助手，有什么可以帮你的？\n\n"
        f"📊 当前预设：**{preset['description']}**\n\n"
        f"💡 点击输入框上方的 ⚙ 按钮切换预设"
    ).send()


def _apply_preset(settings):
    raw = settings.get("preset", "instruct_general")
    target = resolve_preset_name(raw)
    if target not in PRESETS:
        return None
    cl.user_session.set("current_preset", target)
    return target


@cl.on_settings_edit
async def on_settings_edit(settings):
    _apply_preset(settings)


@cl.on_settings_update
async def on_settings_update(settings):
    target = _apply_preset(settings)
    if target is None:
        return
    p = get_preset(target)
    await cl.Message(
        content=f"✅ 已切换：**{p['description']}**\n"
        f"🌡 temp={p['temperature']} | top_p={p['top_p']} | penalty={p['presence_penalty']}"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    if not message.content or not message.content.strip():
        return

    current_preset_name = cl.user_session.get("current_preset")
    preset, api_params, adapted_extra = build_preset_info(current_preset_name)

    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": message.content})
    messages = truncate_messages(messages)
    cl.user_session.set("messages", messages)

    msg = cl.Message(content="")
    await msg.send()

    try:
        stream = client.chat.completions.create(
            model="qwen",
            messages=messages,
            max_tokens=16384,
            stream=True,
            **api_params,
            extra_body=adapted_extra,
        )

        full_content = []
        reasoning_parts = []
        await _stream_separate(stream, msg, full_content, reasoning_parts)

        await msg.update()
        assistant_msg = {"role": "assistant", "content": "".join(full_content)}
        messages.append(assistant_msg)

    except Exception as e:
        await msg.update()
        await cl.Message(content=f"⚠ 请求失败: {e}").send()
        import traceback
        traceback.print_exc()


async def _stream_separate(stream, msg, full_content, reasoning_parts):
    thinking_step = None

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        rc = getattr(delta, "reasoning_content", None)
        content = delta.content

        if rc:
            reasoning_parts.append(rc)
            if thinking_step is None:
                thinking_step = cl.Step(
                    name="💭 思考过程",
                    type="run",
                    auto_collapse=True,
                    default_open=False,
                )
                await thinking_step.send()
            await thinking_step.stream_token(rc)

        if content:
            full_content.append(content)
            await msg.stream_token(content)

    if thinking_step:
        await thinking_step.send()
