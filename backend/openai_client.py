"""
Shared AsyncOpenAI singleton for the entire backend.

All modules must import via:
    from openai_client import get_async_openai

Do NOT instantiate AsyncOpenAI anywhere else. One client = one connection
pool = no fragmentation across the 19 modules that previously each held
their own sync OpenAI() instance.

The client is lazy-initialised on first call so module import never
triggers network activity or requires the event loop to be running.
"""

import os
from typing import Optional
from openai import AsyncOpenAI

_client: Optional[AsyncOpenAI] = None


def get_async_openai() -> AsyncOpenAI:
    """Return the shared AsyncOpenAI client, creating it on first call."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client
