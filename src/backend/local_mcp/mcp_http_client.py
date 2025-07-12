import httpx
from local_mcp.mcp_models import McpModel
from typing import List

class McpHttpClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def list_models(self) -> List[McpModel]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/v1/models")
            response.raise_for_status()
            return [McpModel(**model) for model in response.json()]