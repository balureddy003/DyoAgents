"""
LlamaIndex provider for MagenticOne-compatible AutoGen agent.

Wraps a LlamaIndex index or query-engine so it can respond to text queries.

Supports:
    - `.query(question:str)`
    - `.async_query(question:str)`
    - `.as_query_engine()`

Also includes a utility to load a Chroma index for use with local Docker-based LLMs.
"""

from __future__ import annotations

import os
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
import anyio
from typing import Any, Callable, Optional

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.chroma import ChromaVectorStore
from chromadb import PersistentClient

# --- AutoGen base classes ----------------------------------------------------
from autogen_core import BaseAgent

# --- AutoGen TextMessage shim (for compatibility) ----------------------------
try:
    from autogen_core.messages import TextMessage  # type: ignore
except ImportError:
    class TextMessage:
        def __init__(self, content: str, source: str = "LlamaIndexProvider"):
            self.content = content
            self.source = source
# -----------------------------------------------------------------------------


class LlamaIndexProvider(BaseAgent):
    """
    A thin wrapper turning a LlamaIndex index / query-engine into an AutoGen agent.
    """

    def __init__(self, index: Any, **kwargs: Any):
        if index is None:
            raise ValueError("LlamaIndexProvider received None as index.")
        super().__init__(description="RAG knowledge base (LlamaIndex)", **kwargs)
        self._query_fn: Callable[[str], Any] = self._normalise_index(index)

    @staticmethod
    def _normalise_index(index_obj: Any) -> Callable[[str], Any]:
        """
        Convert various LlamaIndex objects into a uniform sync `query(text)` call.
        """
        if callable(getattr(index_obj, "query", None)):
            return index_obj.query
        if callable(getattr(index_obj, "as_query_engine", None)):
            engine = index_obj.as_query_engine()
            if callable(getattr(engine, "query", None)):
                return engine.query
        raise TypeError("Unsupported index or query-engine object supplied.")

    async def ask(self, msg: TextMessage, **ctx) -> TextMessage:
        """Handle a text message query."""
        question = msg.content
        answer = await anyio.to_thread.run_sync(self._query_fn, question)
        return TextMessage(content=str(answer), source=self.name)

    async def on_message_impl(self, message, ctx):
        return await self.ask(message)


from typing import Optional

def load_index_from_chroma(
    persist_dir: str = "./chroma_rag_index", collection_name: str = "rag-data"
) -> Optional[VectorStoreIndex]:
    """
    Load an existing Chroma index using the local embedded client (not client/server mode).
    """
    import os
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings
    from llama_index.core import StorageContext, load_index_from_storage
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from chromadb import PersistentClient

    os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

    # Set embedding model
    Settings.llm = None  # ✅ Disable LLM to avoid OpenAI usage
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Set up Chroma client and vector store
    client = PersistentClient(path=persist_dir)
    vector_store = ChromaVectorStore(
        chroma_collection=client.get_or_create_collection(name=collection_name)
    )

    # ✅ Load storage context with persist_dir
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        persist_dir=persist_dir
    )

    try:
        # ✅ Now load index from that context
        index = load_index_from_storage(storage_context=storage_context)
        return index
    except Exception as e:
        print(f"Failed to load index after build: {e}")
        return None

def build_index_and_persist(
    documents_dir: str = "./data",
    persist_dir: str = "./chroma_rag_index",
    collection_name: str = "rag-data"
):
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.core import Settings
    from chromadb import PersistentClient

    os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

    # Set embedding model
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Load documents
    documents = SimpleDirectoryReader(documents_dir).load_data()

    # Prepare Chroma vector store
    client = PersistentClient(path=persist_dir)
    vector_store = ChromaVectorStore(
        chroma_collection=client.get_or_create_collection(name=collection_name)
    )

    # Create index and persist via storage_context
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    # ✅ Correct persistence call
    storage_context.persist(persist_dir=persist_dir)

    return index