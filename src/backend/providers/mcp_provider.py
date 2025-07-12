"""
A thin proxy that lets agents call your TypeScript MCP helpers
through a local FastAPI micro-service.
"""
import httpx
from autogen_core import BaseAgent

# TextMessage location differs across autogen-core versions
try:
    from autogen_core.messages import TextMessage  # ≥ 0.5.8
except ImportError:  # < 0.5.8 – fall‑back shim so the rest of the code keeps working
    class TextMessage:  # minimal stub
        def __init__(self, content: str, source: str = "MCPProvider", **kwargs):
            self.content = content
            self.source = source
            # allow arbitrary extra attributes so callers don’t break
            for k, v in kwargs.items():
                setattr(self, k, v)

class MCPProvider(BaseAgent):
    def __init__(self, base_url="http://localhost:7000/mcp", name="MCPAction", **kw):
        super().__init__(name=name, description="Foundry / GitHub / Ollama actions", **kw)
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30)

    async def ask(self, msg: TextMessage, **ctx) -> TextMessage:
        resp = await self.client.post(f"{self.base_url}/exec",
                                      json={"cmd": msg.content})
        resp.raise_for_status()
        return TextMessage(content=resp.text, source=self.name)

    async def on_message_impl(self, message, ctx):
        return await self.ask(message)