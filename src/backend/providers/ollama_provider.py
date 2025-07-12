import logging
import json
logger = logging.getLogger(__name__)

from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core.models import UserMessage

class OllamaProvider:
    def __init__(self, model: str = "mistral:instruct", base_url: str = "http://localhost:11434/v1"):
        self.model = model
        self.base_url = base_url
        logger.info(f"Initializing OllamaProvider with model '{model}' at '{base_url}'")
        self.client = OllamaChatCompletionClient(model=model, base_url=base_url)

    def _normalize_messages(self, messages):
        normalized = []
        for m in messages:
            role = getattr(m, "source", getattr(m, "role", "user"))
            content = getattr(m, "content", m if isinstance(m, str) else "")
            normalized.append(UserMessage(content=content, source=role))
        return normalized

    async def create(self, messages: list, **kwargs):
        import re
        logger.debug(f"OllamaProvider.create called with {len(messages)} messages")
        user_messages = self._normalize_messages(messages)
        tool_choice = kwargs.pop("tool_choice", "auto")
        tools = kwargs.pop("tools", None)
        kwargs.setdefault("temperature", 0.3)
        kwargs.setdefault("top_p", 0.8)
        response = await self.client.create(user_messages, tools=tools, tool_choice=tool_choice, **kwargs)
        content = response.content.strip()
        match = re.search(r"^.*?[.!?](?:\s|$)", content)
        brief = match.group(0).strip() if match else content.splitlines()[0]
        result = {
            "type": "chat_message",
            "role": "assistant",
            "content": brief,
            "full_content": content,
            "source": "ollama",
            "is_terminated": True
        }
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.debug(f"Tool calls detected: {[t.name for t in response.tool_calls]}")
            result["tool_calls"] = response.tool_calls
            result["tool_responses"] = []

            for call in response.tool_calls:
                try:
                    func_name = call.function.name
                    arguments = json.loads(call.function.arguments)

                    result_value = self.dispatch_tool_call(func_name, arguments)
                    logger.info(f"Executed tool '{func_name}' with result: {result_value}")
                    result["tool_responses"].append({
                        "name": func_name,
                        "result": result_value
                    })
                except Exception as e:
                    logger.error(f"Failed to process tool call '{call.function.name}': {e}")
        return result

    async def create_stream(self, messages: list, **kwargs):
        import re
        logger.debug(f"OllamaProvider.create_stream called with {len(messages)} messages")
        user_messages = self._normalize_messages(messages)
        tool_choice = kwargs.pop("tool_choice", "auto")
        tools = kwargs.pop("tools", None)
        kwargs.setdefault("temperature", 0.3)
        kwargs.setdefault("top_p", 0.8)
        yielded = False
        async for chunk in self.client.create_stream(user_messages, tools=tools, tool_choice=tool_choice, **kwargs):
            content = chunk.content.strip()
            match = re.search(r"^.*?[.!?](?:\s|$)", content)
            if match:
                content = match.group(0).strip()
                yielded = True
                yield {
                    "type": "chat_message",
                    "role": "assistant",
                    "content": content,
                    "source": "ollama",
                    "is_terminated": True
                }
                return
        if not yielded:
            yield {
                "type": "chat_message",
                "role": "assistant",
                "content": "[no response]",
                "source": "ollama",
                "is_terminated": True
            }

    async def close(self):
        await self.client.close()

    def get_client(self, model=None):
        if model and model != self.model:
            logger.info(f"Switching Ollama model from '{self.model}' to '{model}'")
            self.model = model
            self.client = OllamaChatCompletionClient(model=model, base_url=self.base_url)
        return self.client

  

    def dispatch_tool_call(self, name: str, args: dict):
        logger.info(f"Dispatching tool call: {name}({args})")

        # FORCE all tool calls via MCP proxy — do NOT check for local methods
        logger.info(f"Bypassing local method. Proxying tool call: {name}({args}) to MCP")

        # Log the tool name received for MCP proxy
        logger.warning(f"Tool name received for MCP proxy: '{name}'")

        # 2. Try MCP proxy fallback with normalization
        try:
            import subprocess
            import os
            from pathlib import Path
            backend_dir = Path(__file__).resolve().parent.parent
            mcp_path = backend_dir / "mcp_server.py"

            tool_name = name.lower().replace(" ", "_")
            logger.info(f"Normalized tool name: {tool_name}")
            request = {"tool": tool_name, "args": args}
            proc = subprocess.Popen(
                ["python3", str(mcp_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(input=json.dumps(request))
            if proc.returncode != 0:
                logger.error(f"Tool execution failed: {stderr.strip()}")
                return f"[MCP subprocess error: {stderr.strip()}]"
            return stdout.strip()
        except Exception as e:
            logger.error(f"Error proxying tool '{name}' to MCP: {e}")
            return f"[MCP proxy error: {e}]"