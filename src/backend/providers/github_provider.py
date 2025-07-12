from .base import BaseProvider

class GitHubProvider(BaseProvider):
    async def generate(self, prompt: str, model: str, **kwargs):
        if not model:
            raise ValueError("Model is required for GitHubProvider")
        
        return {
            "provider": "github",
            "model": model,
            "response": f"GitHub model responded to: {prompt}"
        }