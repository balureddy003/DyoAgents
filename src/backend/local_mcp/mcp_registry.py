import aiohttp
import logging
from typing import List, Optional
from pydantic import BaseModel

class McpModel(BaseModel):
    id: str
    label: str
    description: Optional[str] = ""

class McpRegistry:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def list_models(self) -> List[McpModel]:
        url = f"{self.base_url}/mcp/models"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return [McpModel(**model) for model in data.get("models", [])]
        except Exception as e:
            logging.error(f"Failed to list MCP models: {e}")
            return []