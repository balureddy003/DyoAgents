from providers.azure_openai_provider import AzureOpenAIProvider
from providers.ollama_provider import OllamaProvider
from providers.docker_provider import DockerProvider
from providers.github_provider import GitHubProvider
from providers.foundry_local_provider import FoundryLocalProvider
from providers.llamaindex_provider import LlamaIndexProvider
from providers.mcp_provider import MCPProvider
from providers.ai_foundry_provider import AiFoundryProvider
import os
PROVIDERS = {
    "docker": DockerProvider(
        base_url="http://localhost:12434/engines/llama.cpp/v1/chat"
    ).get_client(),
    "llamaindex": LlamaIndexProvider,
    "mcp": MCPProvider,
 "AIFOUNDRY_PROVIDER":AiFoundryProvider(
    base_url="http://localhost:5273/v1",  # or wherever Foundry is running
    model="foundry/Phi-3-mini-4k-instruct-generic-gpu"  # Update with your deployed model
),
"OllamaProvider":OllamaProvider(base_url= os.getenv("LLM_URL", "http://localhost:4000/v1"),  # or wherever Foundry is running
    model= os.getenv("DEFAULT_MODEL", "mistral:instruct")  # Update with your deployed model)
)
}