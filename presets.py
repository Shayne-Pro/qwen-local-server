#!/usr/bin/env python3
"""Sampling parameter presets for Qwen models.

Official recommended configurations from Qwen3.6 documentation.
Each preset includes: temperature, top_p, top_k, min_p, presence_penalty, repetition_penalty.

Usage:
    from presets import get_preset, list_presets
    params = get_preset()          # default: instruct_general
    params = get_preset("thinking_coding")

    # Or via environment variable:
    # LLM_PRESET=thinking_general python app.py
"""

import os

PRESETS = {
    "thinking_general": {
        "description": "通用任务的思考模式 — 适合需要深度推理的通用任务",
        "mode": "thinking",
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
    },
    "thinking_coding": {
        "description": "精确编码任务的思考模式 — 适合代码生成和精确编程",
        "mode": "thinking",
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0,
    },
    "instruct_general": {
        "description": "通用任务的 Instruct（非思考）模式 — 适合日常聊天和一般任务",
        "mode": "instruct",
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
    },
    "instruct_reasoning": {
        "description": "推理任务的 Instruct（非思考）模式 — 适合需要推理的非思考场景",
        "mode": "instruct",
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
    },
}

DEFAULT_PRESET = "instruct_general"


def get_preset(name=None):
    """Get a preset by name. Falls back to LLM_PRESET env var, then DEFAULT_PRESET."""
    if name is None:
        name = os.environ.get("LLM_PRESET", DEFAULT_PRESET)
    if name not in PRESETS:
        raise ValueError(
            f"Unknown preset '{name}'. Available: {list(PRESETS.keys())}"
        )
    return PRESETS[name]


def list_presets():
    """Return all preset names with descriptions."""
    return {k: v["description"] for k, v in PRESETS.items()}


def preset_to_api_params(preset):
    """Convert a preset dict to OpenAI API call parameters.

    Returns (params, extra_body) tuple:
      - params: standard OpenAI parameters (temperature, top_p, presence_penalty)
      - extra_body: non-standard parameters passed via extra_body (top_k, min_p, repetition_penalty)
    """
    params = {
        "temperature": preset["temperature"],
        "top_p": preset["top_p"],
        "presence_penalty": preset["presence_penalty"],
    }
    extra_body = {
        "top_k": preset["top_k"],
        "min_p": preset["min_p"],
        "repetition_penalty": preset["repetition_penalty"],
    }
    return params, extra_body
