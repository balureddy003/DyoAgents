from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from autogen_core.model_context import BufferedChatCompletionContext

MAGENTIC_ONE_ORCHESTRATOR_DESCRIPTION = "Main task router and orchestrator agent."
MAGENTIC_ONE_ORCHESTRATOR_SYSTEM_MESSAGE = """
You are the central orchestrator. Based on task type, delegate work to the appropriate agent.
"""

class MagenticOneOrchestratorAgent(AssistantAgent):
    def __init__(self, name: str, model_client: ChatCompletionClient):
        super().__init__(
            name=name,
            model_client=model_client,
            description=MAGENTIC_ONE_ORCHESTRATOR_DESCRIPTION,
            system_message=MAGENTIC_ONE_ORCHESTRATOR_SYSTEM_MESSAGE,
            model_context=BufferedChatCompletionContext(buffer_size=6),
            reflect_on_tool_use=True,
            model_client_stream=True
        )
