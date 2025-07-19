from autogen_agentchat.agents import UserProxyAgent

MAGENTIC_ONE_PROXY_DESCRIPTION = "Simulates user input and allows interactive orchestration testing."

class MagenticOneProxyAgent(UserProxyAgent):
    def __init__(self, name: str, system_message: str = "", description: str = "",  **kwargs):
        super().__init__(
            name=name,
            description=description or MAGENTIC_ONE_PROXY_DESCRIPTION,
              **kwargs
        )
