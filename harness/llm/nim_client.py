from __future__ import annotations

import os

from openai import OpenAI


DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"


def get_nim_api_key(explicit: str | None = None) -> str:
    key = (
        explicit
        # Allow OpenAI-style env var naming (common in notebooks/secrets)
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("NIM_API_KEY")
        or os.environ.get("NVIDIA_API_KEY")
        or os.environ.get("NVAPI_KEY")
    )
    if not key:
        raise ValueError(
            "Missing API key. Set one of: OPENAI_API_KEY, NIM_API_KEY (preferred), NVIDIA_API_KEY, NVAPI_KEY."
        )
    return key


def get_base_url(explicit: str | None = None) -> str:
    return explicit or os.environ.get("OPENAI_BASE_URL") or DEFAULT_NIM_BASE_URL


def get_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    return OpenAI(base_url=get_base_url(base_url), api_key=get_nim_api_key(api_key))


def chat(
    *,
    prompt: str,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
    max_tokens: int = 2048,
) -> str:
    client = get_client(api_key=api_key, base_url=base_url)
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return r.choices[0].message.content or ""

