from .base import BaseProvider
import httpx

class AzureOpenAIProvider(BaseProvider):
    async def generate(self, prompt: str, model: str, **kwargs):
        if not model:
            raise ValueError("Model is required for AzureOpenAIProvider")
        
        url = f"{self.api_url}/openai/deployments/{model}/completions?api-version=2023-03-15-preview"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 200)
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()