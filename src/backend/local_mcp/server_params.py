# src/backend/mcp/server_params.py

from pydantic import BaseModel
from typing import List, Optional, Dict

class StdioServerParameters(BaseModel):
    command: str
    args: Optional[List[str]] = []
    env: Optional[Dict[str, str]] = {}