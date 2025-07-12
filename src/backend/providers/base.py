

from dataclasses import dataclass
from typing import Optional, ClassVar, Dict, Any

@dataclass
class ProviderMessage:
    # Add a class-level unique type identifier string for MessageFactory
    type: ClassVar[str] = "providers.base.ProviderMessage"

    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            role=d.get("role", ""),
            content=d.get("content", ""),
            metadata=d.get("metadata", None),
        )

class BaseProvider:
    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url
        self.api_key = api_key

    async def generate(self, prompt: str, model: str, **kwargs) -> ProviderMessage:
        """
        This must be implemented in all provider subclasses.
        """
        raise NotImplementedError("Provider must implement generate()")

    async def list_models(self):
        """
        Can be overridden to return available models.
        """
        return []