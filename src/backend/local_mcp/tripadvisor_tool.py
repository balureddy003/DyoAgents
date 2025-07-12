# backend/local_mcp/tripadvisor_tool.py
from autogen.agentchat.contrib.tool_utils import BaseTool

class TripAdvisorTool(BaseTool):
    def __init__(self):
        super().__init__(name="trip_advisor_tool", description="Fetch trip data.")

    def run(self, query: str) -> str:
        return f"TripAdvisor response for: {query}"