from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient
from autogen_core.model_context import BufferedChatCompletionContext
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizableTextQuery
from azure.identity import DefaultAzureCredential
from autogen_agentchat.messages import StructuredMessage
from pydantic import BaseModel
from typing import Literal

MAGENTIC_ONE_RAG_DESCRIPTION = "An agent that has access to internal index and can handle RAG tasks. Call this agent if you are getting questions on your internal index."

MAGENTIC_ONE_RAG_SYSTEM_MESSAGE = """
You are a helpful AI Assistant.
When given a user query, use available tools to help the user with their request.
Reply \"TERMINATE\" in the end when everything is done.
"""

class RAGResponse(BaseModel):
    source: str
    content: str

class MagenticOneRAGAgent(AssistantAgent):
    """An agent used by MagenticOne that provides RAG capabilities using an Azure Cognitive Search index.

    The prompts and description are sealed, to replicate the original MagenticOne configuration.
    """

    def __init__(
        self,
        name: str,
        model_client: ChatCompletionClient,
        index_name: str,
        AZURE_SEARCH_SERVICE_ENDPOINT: str,
        description: str = MAGENTIC_ONE_RAG_DESCRIPTION,
    ):
        super().__init__(
            name=name,
            model_client=model_client,
            description=description,
            system_message=MAGENTIC_ONE_RAG_SYSTEM_MESSAGE,
            tools=[self.do_search],
            output_content_type=RAGResponse,
            reflect_on_tool_use=True,
            model_client_stream=True,
            model_context=BufferedChatCompletionContext(buffer_size=5)
        )

        self.index_name = index_name
        self.AZURE_SEARCH_SERVICE_ENDPOINT = AZURE_SEARCH_SERVICE_ENDPOINT

    def config_search(self) -> SearchClient:
        index_name = self.index_name
        credential = DefaultAzureCredential()
        return SearchClient(
            endpoint=self.AZURE_SEARCH_SERVICE_ENDPOINT,
            index_name=index_name,
            credential=credential,
        )

    async def do_search(self, query: str) -> RAGResponse:
        """Search indexed data using Azure Cognitive Search with vector-based queries."""
        search_client = self.config_search()
        fields = "text_vector"  # Ensure this matches the actual vector field in your index
        vector_query = VectorizableTextQuery(
            text=query,
            k_nearest_neighbors=1,
            fields=fields,
            exhaustive=True,
        )

        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["parent_id", "chunk_id", "chunk"],  # Match to your schema
            top=1,
        )

        answer = ""
        for result in results:
            answer += result.get("chunk", "")

        return RAGResponse(source="AzureCognitiveSearch", content=answer)