import httpx
import asyncio
from typing import AsyncGenerator

async def sse_connect(url: str) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("GET", url, headers={"Accept": "text/event-stream"}) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line.removeprefix("data: ").strip()