from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient

# TODO: Add validation for custom agent configuration inputs
class MagenticOneCustomAgent(AssistantAgent):
    """
    A general-purpose assistant agent used by MagenticOne.
    This version is aligned with the provider-based architecture and supports future extensibility.
    """

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        system_message: str,
        description: str,
        tools=None,  # Optional list of tools
        user_id: str = None,
        output_content_type=None,
    ):
        from autogen_core.model_context import BufferedChatCompletionContext

        super().__init__(
            name=name,
            model_client=model_client,
            description=description,
            system_message=system_message,
            tools=tools,
            reflect_on_tool_use=True,
            model_client_stream=True,
            max_tool_iterations=3,
            output_content_type=output_content_type,
            model_context=BufferedChatCompletionContext(buffer_size=5),
        )
        self.user_id = user_id