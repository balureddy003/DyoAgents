from autogen_agentchat.agents import UserProxyAgent

MAGENTIC_ONE_PROXY_DESCRIPTION = "Simulates user input and allows interactive orchestration testing."

class MagenticOneProxyAgent(UserProxyAgent):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            description=MAGENTIC_ONE_PROXY_DESCRIPTION,
            is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", "")
        )
