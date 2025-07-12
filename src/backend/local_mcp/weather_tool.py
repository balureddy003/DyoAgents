# backend/local_mcp/weather_tool.py
from autogen.agentchat.contrib.tool_utils import BaseTool

class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(name="weather_tool", description="Get weather info.")

    def run(self, location: str) -> str:
        return f"Weather for {location}: Sunny 25°C"