from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class CallToolResult(BaseModel):
    name: str
    arguments: Dict[str, Any]
    result: Optional[Any]

class ListToolsResult(BaseModel):
    tools: List[str]