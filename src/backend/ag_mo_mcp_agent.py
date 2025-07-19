import os
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import (
    ChatCompletionClient,
)
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.tools.mcp import SseMcpToolAdapter, StdioServerParams, StdioMcpToolAdapter, SseServerParams

from autogen_agentchat.messages import ToolCallExecutionEvent, TextMessage


import logging
logger = logging.getLogger(__name__)

class MagenticOneCustomMCPAgent(AssistantAgent):
    """An agent used by MagenticOne that provides coding assistance using an LLM model client.
    
    The prompts and description are sealed to replicate the original MagenticOne configuration.
    See AssistantAgent if you wish to modify these values.
    """
    
    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        system_message: str,
        description: str,
        adapter,  # adapter is now provided by the async factory method
        user_id: str = None
    ):
        super().__init__(
            name,
            model_client,
            description=description,
            system_message=system_message,
            tools=adapter,
            reflect_on_tool_use=True,
            max_tool_iterations=3
        )
        self.model_client = model_client
        self.tool_cache = {}
        self.tool_call_limit = 1
        self.user_id = user_id
    
    async def on_function_call(self, tool_name, arguments):
        cache_key = f"{tool_name}:{str(arguments)}"

        if cache_key in self.tool_cache:
            logger.debug(f"[Tool Cache Hit] {cache_key}")
            return self.tool_cache[cache_key]

        try:
            logger.info(f"[Function Call] Executing: {tool_name} with {arguments}")
            result = await super().on_function_call(tool_name, arguments)

            # Enforce that a real tool result is returned and contains meaningful content
            if isinstance(result, ToolCallExecutionEvent) and result.content:
                # Validate that content is a list of dicts with "text" fields (as expected from MCP)
                if isinstance(result.content, list) and all(isinstance(entry, dict) and "text" in entry for entry in result.content):
                    logger.debug(f"[Validated Tool Result] {result.content}")
                    self.tool_cache[cache_key] = result
                    return result
                else:
                    logger.warning(f"[Invalid Tool Result Structure] {result.content}")
                    raise RuntimeError(f"Tool {tool_name} returned unexpected format.")
            else:
                logger.warning(f"[Tool Result Missing or Invalid for {tool_name}] Fallback/hallucination is not allowed.")
                raise RuntimeError(f"Tool {tool_name} failed to return valid result.")
        except Exception as e:
            logger.error(f"[Function Call Error] {e}")
            raise


    @classmethod
    async def create(
        cls,
        name: str,
        model_client: ChatCompletionClient = None,
        system_message: str = "",
        description: str = "",
        user_id: str = None
    ):
        if model_client is None:
            model_client = OllamaChatCompletionClient(config={"model": "mistral"})
            if not model_client.supports_function_calling():
                raise RuntimeError("The configured model does not support function calling required for tools.")

        logger.info("Creating MagenticOneCustomMCPAgent...")
        logger.debug(f"MCP_SERVER_URI: {os.environ.get('MCP_SERVER_URI')}")
        logger.debug(f"MCP_SERVER_API_KEY: {os.environ.get('MCP_SERVER_API_KEY')}")

        server_mode = os.environ.get("MCP_SERVER_MODE", "sse").lower()
        logger.debug(f"MCP_SERVER_MODE: {server_mode}")

        if server_mode == "stdio":
            server_params = StdioServerParams(
                command="python",
                args=["mcp/mcp_general_server.py"],
                env={
                    "AZURE_COMMUNICATION_EMAIL_ENDPOINT": os.getenv("AZURE_COMMUNICATION_EMAIL_ENDPOINT"),
                    "AZURE_COMMUNICATION_EMAIL_SENDER": os.getenv("AZURE_COMMUNICATION_EMAIL_SENDER"),
                    "AZURE_COMMUNICATION_EMAIL_RECIPIENT_DEFAULT": os.getenv("AZURE_COMMUNICATION_EMAIL_RECIPIENT_DEFAULT"),
                    "AZURE_COMMUNICATION_EMAIL_SUBJECT_DEFAULT": os.getenv("AZURE_COMMUNICATION_EMAIL_SUBJECT_DEFAULT"),
                    "AZURE_CLIENT_ID": os.getenv("AZURE_CLIENT_ID"),
                },
            )
        else:
            mcp_server_uri = os.environ.get("MCP_SERVER_URI", "http://localhost:8333") + "/sse"
            logger.info(f"Using SSE MCP Server URI: {mcp_server_uri}")
            server_params = SseServerParams(
                url=mcp_server_uri,
                headers={"x-api-key": os.environ.get("MCP_SERVER_API_KEY", "1234")}
            )

        try:
            if server_mode == "stdio":
                logger.info("Initializing adapters using STDIO mode...")
                adapter_data_provider = await StdioMcpToolAdapter.from_server_params(server_params, "data_provider")
                adapter_data_list_tables = await StdioMcpToolAdapter.from_server_params(server_params, "show_tables")
                adapter_mailer = await StdioMcpToolAdapter.from_server_params(server_params, "mailer")
            else:
                logger.info("Initializing adapters using SSE mode...")
                adapter_data_provider = await SseMcpToolAdapter.from_server_params(server_params, "data_provider")
                adapter_data_list_tables = await SseMcpToolAdapter.from_server_params(server_params, "show_tables")
                adapter_mailer = await SseMcpToolAdapter.from_server_params(server_params, "mailer")
        except Exception as e:
            logger.error(f"[Adapter Initialization Error] {e}")
            raise

        logger.info("Adapters initialized:")
        logger.debug(f"  Data Provider Adapter: {adapter_data_provider}")
        logger.debug(f"  Data List Tables Adapter: {adapter_data_list_tables}")
        logger.debug(f"  Mailer Adapter: {adapter_mailer}")
        logger.debug(f"Server mode used: {server_mode}")

        from autogen_core.model_context import BufferedChatCompletionContext
        model_context = BufferedChatCompletionContext(buffer_size=5)

        return cls(
            name,
            model_client,
            system_message,
            description,
            [adapter_data_provider, adapter_data_list_tables, adapter_mailer],
            user_id=user_id
        )
