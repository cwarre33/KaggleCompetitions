"""NVIDIA NIM API client - OpenAI-compatible chat completions."""
import os
from openai import OpenAI

# NIM base URL - OpenAI compatible
NIM_BASE = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "meta/llama-3.1-8b-instruct"


def get_nim_client(api_key: str | None = None) -> OpenAI:
    """Create OpenAI client configured for NIM API."""
    key = api_key or os.environ.get("NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY") or os.environ.get("NVAPI_KEY")
    if not key:
        raise ValueError("Set NIM_API_KEY or NVIDIA_API_KEY in .env")
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=key,
    )


def chat(prompt: str, model: str = DEFAULT_MODEL, api_key: str | None = None) -> str:
    """Send prompt to NIM and return assistant message."""
    client = get_nim_client(api_key)
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.3,
    )
    return r.choices[0].message.content
