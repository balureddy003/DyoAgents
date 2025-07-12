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
    ):
        super().__init__(
            name=name,
            model_client=model_client,
            description=description,
            system_message=system_message,
            tools=tools,
        )
        self.user_id = user_id