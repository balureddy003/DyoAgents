import json
import httpx
from httpx import ReadTimeout, Timeout

class DockerProvider:
    def __init__(
        self,
        base_url: str = None,
        default_model: str = None,
    ):
        self.base_url = base_url or "http://localhost:12434/engines/llama.cpp/v1"
        self.default_model = default_model
        # Include "family" to satisfy multimodal WebSurfer
        self.model_info = {
            "family": "openai",
            "function_calling": True,
            "json_output": True,
            "vision": False,
        }

    def get_client(self, model: str = None):
        """
        Sets the default model and returns this provider instance.
        """
        self.default_model = model or self.default_model
        return self

    async def create(self, messages: list, model: str = None, **kwargs):
        model = model or self.default_model
        if not model:
            raise ValueError("Model must be provided for DockerProvider.create()")
        # flatten chat messages into an OpenAI‑style prompt
        lines = []
        for m in messages:
            role = getattr(m, "role", getattr(m, "source", "user"))
            content = getattr(m, "content", "")
            lines.append(f"{role}: {content}")
        prompt = "\n".join(lines) + "\nassistant:"
        """
        Proxy to /completions; same signature as OpenAI.
        Returns the response JSON dict.
        """
        # ensure we never double up a /chat segment
        base = self.base_url.rstrip("/")
        base = base.replace("/chat", "")
        url = f"{base}/completions"
        serializable_kwargs = {}
        for k, v in kwargs.items():
            try:
                json.dumps(v)
                serializable_kwargs[k] = v
            except (TypeError, OverflowError):
                # skip non-serializable values like CancellationToken
                continue
        payload = {"model": model, "prompt": prompt, **serializable_kwargs}
        print("POST", url, payload)
        timeout = Timeout(connect=10.0, read=300.0, write=300.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                res = await client.post(url, json=payload)
            except ReadTimeout:
                # retry once on tmagentic_one_orchestrator.pyimeout
                res = await client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
            if not isinstance(data, dict) or "choices" not in data or not data["choices"]:
                raise ValueError("Unexpected response structure: missing 'choices'")
            text = data["choices"][0].get("text")
            if not isinstance(text, str):
                text = str(text) if text is not None else "[no response from model]"
            text = text.strip()
            return {
                "type": "chat_message",
                "role": "assistant",
                "content": text,
                "name": "DockerProvider",
                "source": "docker"
            }

    async def create_stream(self, messages: list, model: str = None, **kwargs):
        model = model or self.default_model
        if not model:
            raise ValueError("Model must be provided for DockerProvider.create_stream()")
        # flatten chat messages into an OpenAI‑style prompt
        lines = []
        for m in messages:
            role = getattr(m, "role", getattr(m, "source", "user"))
            content = getattr(m, "content", "")
            lines.append(f"{role}: {content}")
        prompt = "\n".join(lines) + "\nassistant:"
        """
        Proxy streaming completions; yields chunk dicts like OpenAI.
        """
        # ensure we never double up a /chat segment
        base = self.base_url.rstrip("/")
        base = base.replace("/chat", "")
        url = f"{base}/completions"
        serializable_kwargs = {}
        for k, v in kwargs.items():
            try:
                json.dumps(v)
                serializable_kwargs[k] = v
            except (TypeError, OverflowError):
                # skip non-serializable values like CancellationToken
                continue
        payload = {"model": model, "prompt": prompt, "stream": True, **serializable_kwargs}
        timeout = Timeout(connect=10.0, read=300.0, write=300.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                streamer = client.stream("POST", url, json=payload)
            except ReadTimeout:
                # retry once on timeout
                streamer = client.stream("POST", url, json=payload)
            yielded = False
            async with streamer as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    text = chunk.get("choices", [{}])[0].get("text")
                    if not isinstance(text, str):
                        text = str(text) if text is not None else "[no response from model]"
                    text = text.strip()
                    if text:
                        yielded = True
                        yield {
                            "type": "chat_message",
                            "role": "assistant",
                            "content": text,
                            "source": "docker"
                        }
                if not yielded:
                    yield {
                        "type": "chat_message",
                        "role": "assistant",
                        "content": "[no result]",
                        "source": "docker"
                    }