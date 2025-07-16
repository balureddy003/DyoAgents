from autogen_agentchat.agents import AssistantAgent
from autogen_core.model_context import BufferedChatCompletionContext
from autogen_core.models import ChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

MAGENTIC_ONE_WEB_SURFER_DESCRIPTION = "Surf the web for up-to-date answers when internal RAG is insufficient."
MAGENTIC_ONE_WEB_SURFER_SYSTEM_MESSAGE = """
Use web search when asked for recent events, news, or external topics not in internal data.
"""

class MagenticOneWebSurferAgent(AssistantAgent):
    def __init__(self, name: str, model_client: ChatCompletionClient):
        super().__init__(
            name=name,
            model_client=model_client,
            description=MAGENTIC_ONE_WEB_SURFER_DESCRIPTION,
            system_message=MAGENTIC_ONE_WEB_SURFER_SYSTEM_MESSAGE,
            tools=[MultimodalWebSurfer()],
            model_context=BufferedChatCompletionContext(buffer_size=4),
            reflect_on_tool_use=True,
            model_client_stream=True
        )
