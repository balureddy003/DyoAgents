# backend/mcp/mcp_tools.py
from autogen_ext.tools.mcp import mcp_server_tools, StdioServerParams, SseServerParams

async def load_mcp_tools(server_params):
    """
    Given StdioServerParams or SseServerParams, returns list of MCP tool adapters.
    """
    tools = await mcp_server_tools(server_params)
    return tools