from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ModelMetadata:
    model: str
    family: str
    api_base: str
    api_key: Optional[str] = None
    api_type: str = "openai"
    vision: bool = False
    json_output: bool = False
    function_calling: bool = False
    structured_output: bool = False

@dataclass
class McpModel:
    label: str
    component_type: str
    version: int
    component_version: int
    description: str
    config: Dict[str, any]