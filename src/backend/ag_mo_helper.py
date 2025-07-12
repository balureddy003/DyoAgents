import asyncio
import logging
import os
import time
from uuid import uuid4
from inspect import signature

from typing import Optional, AsyncGenerator, Dict, Any, List
from autogen_agentchat.ui import Console
from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

from autogen_ext.code_executors.azure import ACADynamicSessionsCodeExecutor
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core import AgentId, AgentProxy, DefaultTopicId
from autogen_core import SingleThreadedAgentRuntime
from autogen_core import CancellationToken

import tempfile

from dotenv import load_dotenv
load_dotenv()

from providers.registry import PROVIDERS
from ag_mo_agent import MagenticOneCustomAgent
from ag_mo_rag_agent import MagenticOneRAGAgent
from ag_mo_mcp_agent import MagenticOneCustomMCPAgent

import re
import uuid
# Helper function to make a valid Python identifier from a name
def make_valid_identifier(name: str) -> str:
    return re.sub(r'\W|^(?=\d)', '_', name)
def _wrap_with_proxy(agent):
    """
    Attach a unique AgentId (id/name + key) to every agent so that
    message.source is never 'unknown'.

    The signatures of *both* AgentId and AgentProxy vary across
    autogen‑core releases.  We therefore:

    1.  Build an AgentId using the first signature that works.
    2.  Inspect AgentProxy.__init__ and create the proxy with
        the appropriate argument names/positions.

    If the object is already an AgentProxy we simply return it.
    """
    if isinstance(agent, AgentProxy):
        return agent  # already wrapped

    new_key = str(uuid4())

    # ---- Step 1: build a compatible AgentId ---------------------------------
    agent_id = None
    for kwargs in (
        {"name": agent.name, "key": new_key},
        {"id": agent.name, "key": new_key},
        {},  # fallback to positional signature tried below
    ):
        try:
            agent_id = AgentId(**kwargs) if kwargs else AgentId(agent.name, new_key)
            break
        except TypeError:
            continue

    if agent_id is None:
        raise RuntimeError("Unable to construct AgentId with the current autogen‑core version.")

    # ---- Step 2: wrap with AgentProxy ---------------------------------------
    sig = signature(AgentProxy)  # reflect current signature
    param_names = list(sig.parameters)

    try:
        if {"agent_id", "agent"}.issubset(param_names):
            proxy = AgentProxy(agent_id=agent_id, agent=agent)
            proxy.name = getattr(agent, "name", str(agent_id))
            # Expose the underlying agent's produced_message_types so GroupChat can inspect it
            if not hasattr(proxy, "produced_message_types"):
                proxy.produced_message_types = getattr(agent, "produced_message_types", [])
            # --- propagate commonly‑used attributes so GroupChat can inspect them ---
            for _attr in ("name", "description", "produced_message_types"):
                if hasattr(agent, _attr) and not hasattr(proxy, _attr):
                    try:
                        setattr(proxy, _attr, getattr(agent, _attr))
                    except Exception:
                        # silently skip if the proxy implementation forbids setting
                        pass
            # --- forward lifecycle / stream handlers the team code expects ---
            for _method in ("on_reset", "on_messages_stream", "on_message"):
                if hasattr(agent, _method) and not hasattr(proxy, _method):
                    try:
                        setattr(proxy, _method, getattr(agent, _method))
                    except Exception:
                        pass
            return proxy
        elif {"id", "agent"}.issubset(param_names):
            proxy = AgentProxy(id=agent_id, agent=agent)
            proxy.name = getattr(agent, "name", str(agent_id))
            # Expose the underlying agent's produced_message_types so GroupChat can inspect it
            if not hasattr(proxy, "produced_message_types"):
                proxy.produced_message_types = getattr(agent, "produced_message_types", [])
            # --- propagate commonly‑used attributes so GroupChat can inspect them ---
            for _attr in ("name", "description", "produced_message_types"):
                if hasattr(agent, _attr) and not hasattr(proxy, _attr):
                    try:
                        setattr(proxy, _attr, getattr(agent, _attr))
                    except Exception:
                        # silently skip if the proxy implementation forbids setting
                        pass
            # --- forward lifecycle / stream handlers the team code expects ---
            for _method in ("on_reset", "on_messages_stream", "on_message"):
                if hasattr(agent, _method) and not hasattr(proxy, _method):
                    try:
                        setattr(proxy, _method, getattr(agent, _method))
                    except Exception:
                        pass
            return proxy
        elif len(param_names) >= 2:
            # assume first two positional parameters are (agent_id/id, agent)
            proxy = AgentProxy(agent_id, agent)
            proxy.name = getattr(agent, "name", str(agent_id))
            # Expose the underlying agent's produced_message_types so GroupChat can inspect it
            if not hasattr(proxy, "produced_message_types"):
                proxy.produced_message_types = getattr(agent, "produced_message_types", [])
            # --- propagate commonly‑used attributes so GroupChat can inspect them ---
            for _attr in ("name", "description", "produced_message_types"):
                if hasattr(agent, _attr) and not hasattr(proxy, _attr):
                    try:
                        setattr(proxy, _attr, getattr(agent, _attr))
                    except Exception:
                        # silently skip if the proxy implementation forbids setting
                        pass
            # --- forward lifecycle / stream handlers the team code expects ---
            for _method in ("on_reset", "on_messages_stream", "on_message"):
                if hasattr(agent, _method) and not hasattr(proxy, _method):
                    try:
                        setattr(proxy, _method, getattr(agent, _method))
                    except Exception:
                        pass
            return proxy
    except TypeError:
        pass

    raise RuntimeError("Unable to construct AgentProxy with the current autogen‑core version.")

def generate_session_name():
    import random
    adjectives = ["quantum", "stellar", "cyber", "astro", "virtual", "cosmic"]
    nouns = ["cyborg", "robot", "drone", "galaxy", "probe", "hologram"]
    return f"{random.choice(adjectives)}-{random.choice(nouns)}-{random.randint(1000,9999)}"

class MagenticOneHelper:
    def __init__(self, logs_dir: str = None, save_screenshots: bool = False, run_locally: bool = False, user_id: str = None, client: Optional[Any] = None) -> None:
        self.logs_dir = logs_dir or os.getcwd()
        self.runtime: Optional[SingleThreadedAgentRuntime] = None
        self.save_screenshots = save_screenshots
        self.run_locally = run_locally
        self.user_id = user_id
        self.provider_name = None
        self.model = None
        self.provider = None
        self.client = client
        self.max_rounds = 50
        self.max_time = 25 * 60
        self.max_stalls_before_replan = 5
        self.return_final_answer = True
        self.start_page = "https://www.bing.com"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)

    async def initialize(self, agents, session_id=None, provider_name: str = "docker", model: str = None) -> None:
        self.runtime = SingleThreadedAgentRuntime()
        self.session_id = session_id or generate_session_name()
        self.provider_name = provider_name
        self.model = model
        if provider_name == "ollama":
            self.client = OllamaChatCompletionClient(model=self.model)
        self.provider = PROVIDERS.get(provider_name)

        if not self.provider:
            raise ValueError(f"Provider {provider_name} not found")

        self.client = self.client or self.provider

        try:
            self.agents = await self.setup_agents(agents, self.client, self.logs_dir)
            if not self.agents:
                raise RuntimeError("No agents were initialized. Please check configuration.")
        except Exception as e:
            raise RuntimeError(f"Agent initialization failed: {e}") from e

    async def setup_agents(self, agents, client, logs_dir):
        agent_list = []
        for agent in agents:
            if agent["type"] == "MagenticOne" and agent["name"] == "Coder":
                agent_list.append(_wrap_with_proxy(MagenticOneCoderAgent("Coder", model_client=client)))
            elif agent["type"] == "MagenticOne" and agent["name"] == "Executor":
                if self.run_locally:
                    executor = CodeExecutorAgent("Executor", code_executor=await DockerCommandLineCodeExecutor(work_dir=logs_dir).start())
                else:
                    endpoint = os.getenv("POOL_MANAGEMENT_ENDPOINT")
                    if not endpoint:
                        executor = CodeExecutorAgent("Executor", code_executor=await DockerCommandLineCodeExecutor(work_dir=logs_dir).start())
                    else:
                        executor = CodeExecutorAgent("Executor", code_executor=ACADynamicSessionsCodeExecutor(pool_management_endpoint=endpoint, credential=DefaultAzureCredential(), work_dir=tempfile.mkdtemp()))
                agent_list.append(_wrap_with_proxy(executor))
            elif agent["type"] == "MagenticOne" and agent["name"] == "WebSurfer":
                # Ensure 'function_calling' key is present in model_info for compatibility
                if getattr(client, "model_info", None) is not None:
                    if "function_calling" not in client.model_info:
                        client.model_info["function_calling"] = True

                agent_list.append(_wrap_with_proxy(MultimodalWebSurfer("WebSurfer", model_client=client)))
            elif agent["type"] == "MagenticOne" and agent["name"] == "FileSurfer":
                file_surfer = FileSurfer("FileSurfer", model_client=client)
                file_surfer._browser.set_path(os.path.join(os.getcwd(), "data"))
                agent_list.append(file_surfer)
            elif agent["type"] == "Custom":
                agent_list.append(_wrap_with_proxy(MagenticOneCustomAgent(agent["name"], client, agent["system_message"], agent["description"])))
            elif agent["type"] == "CustomMCP":
                model_name = self.model or os.getenv("DEFAULT_MODEL", "llama3")
                custom_client = OllamaChatCompletionClient(model=model_name)
                custom_agent = await MagenticOneCustomMCPAgent.create(
                    agent["name"],
                    custom_client,
                    agent["system_message"] + "\n\n in case of email use this address as TO: " + self.user_id,
                    agent["description"],
                    self.user_id
                )
                agent_list.append(_wrap_with_proxy(custom_agent))
                print(f'{agent["name"]} (custom MCP) added!')

            elif agent["type"] == "RAG":
                agent_list.append(_wrap_with_proxy(MagenticOneRAGAgent(agent["name"], model_client=client, index_name=agent["index_name"], description=agent["description"], AZURE_SEARCH_SERVICE_ENDPOINT=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"))))
            else:
                raise ValueError("Unknown Agent!")
        return agent_list

    def main(self, task):
        team = MagenticOneGroupChat(participants=self.agents, model_client=self.client, max_turns=self.max_rounds, max_stalls=self.max_stalls_before_replan, emit_team_events=False)
        self.team = team
        cancellation_token = CancellationToken()
        stream = team.run_stream(task=task, cancellation_token=cancellation_token)
        return stream, cancellation_token

async def main(agents, task, run_locally, provider_name, model) -> None:
    helper = MagenticOneHelper(logs_dir=".", run_locally=run_locally)
    await helper.initialize(agents, provider_name=provider_name, model=model)
    team = MagenticOneGroupChat(participants=helper.agents, model_client=helper.client, max_turns=helper.max_rounds, max_stalls=helper.max_stalls_before_replan)
    try:
        await Console(team.run_stream(task=task))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await team.shutdown()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", "-t", type=str, required=True)
    parser.add_argument("--run_locally", action="store_true")
    parser.add_argument("--provider", type=str, default="ollama")
    parser.add_argument("--model", type=str, required=True)

    args = parser.parse_args()
    MAGENTIC_ONE_DEFAULT_AGENTS = [
        {"input_key": "0001", "type": "MagenticOne", "name": "Coder", "system_message": "", "description": "", "icon": "👨‍💻"},
        {"input_key": "0002", "type": "MagenticOne", "name": "Executor", "system_message": "", "description": "", "icon": "💻"},
        {"input_key": "0003", "type": "MagenticOne", "name": "FileSurfer", "system_message": "", "description": "", "icon": "📂"},
        {"input_key": "0004", "type": "MagenticOne", "name": "WebSurfer", "system_message": "", "description": "", "icon": "🏄‍♂️"},
    ]
    asyncio.run(main(MAGENTIC_ONE_DEFAULT_AGENTS, args.task, args.run_locally, args.provider, args.model))