from autogen_agentchat.agents import CodeExecutorAgent

MAGENTIC_ONE_CODE_EXECUTOR_DESCRIPTION = "Executes code returned by other agents."
MAGENTIC_ONE_CODE_EXECUTOR_SYSTEM_MESSAGE = """
You are a code executor. You only execute code blocks that are passed to you.
Return only execution results. Do not add commentary.
"""

class MagenticOneCodeExecutorAgent(CodeExecutorAgent):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            description=MAGENTIC_ONE_CODE_EXECUTOR_DESCRIPTION,
            system_message=MAGENTIC_ONE_CODE_EXECUTOR_SYSTEM_MESSAGE
        )

    def generate_reply(self, messages, **kwargs):
        for msg in messages:
            if msg.get("role") == "user" and not msg.get("content", "").strip().startswith("```"):
                msg["content"] = f"```python\n{msg['content']}\n```"
        return super().generate_reply(messages, **kwargs)