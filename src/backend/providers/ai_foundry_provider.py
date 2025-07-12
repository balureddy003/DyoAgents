# providers/ai_foundry_provider.py

import httpx
from autogen_agentchat.messages import TextMessage
import logging

logger = logging.getLogger(__name__)


class AiFoundryProvider:
    def __init__(self, base_url="http://localhost:5273/v1", model="Phi-3-mini-4k-instruct-generic-gpu"):
        self.base_url = base_url
        self.default_model = model

        # Required by AutoGen initialization logic
        self.model_info = {
            "model": model,
            "model_id": model,
            "provider": "autogen_ext.models.openai.OpenAIChatCompletionClient",
            "component_type": "model",
            "component_version": 1,
            "version": 1,
            "description": "Azure AI Foundry model",
            "label": "Azure-AI-Foundry",
            "config": {
                "model": model,
                "base_url": base_url,
                "api_type": "azure",
                "api_key": None,
                "json_output": True,
                "structured_output": True,
                "function_calling": False,
                "vision": False,
                "family": "foundry"
            },
            "vision": False
        }

    def get_client(self, model: str = None):
        if model:
            self.default_model = model
            self.model_info["model"] = model.strip().replace("foundry/", "")
        return self

    async def create(self, messages: list, model: str = None, **kwargs):
        try:
            logger.debug(f"[AiFoundryProvider] Entering create() with model={model}, kwargs={kwargs}")
            model = self.default_model.strip().replace("foundry/", "")

            if not messages:
                raise ValueError("Messages list cannot be empty.")
            logger.debug(f"[AiFoundryProvider] Messages received: {[str(m) for m in messages]}")

            temperature = kwargs.get("temperature", 0.7)
            logger.debug(f"[AiFoundryProvider] Temperature set to: {temperature}")
            logger.debug(f"[AiFoundryProvider] Final model used: {model}")

            payload = {
                "model": model,
                "temperature": temperature,
                "messages": [
                    {"role": getattr(m, "role", "user"), "content": getattr(m, "content", str(m))}
                    for m in messages
                ],
                "stream": False
            }

            url = f"{self.base_url}/chat/completions"
            logger.debug(f"[AiFoundryProvider] Posting to URL: {url}")
            logger.debug(f"[AiFoundryProvider] Payload: {payload}")

            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(url, json=payload)

                logger.debug(f"[AiFoundryProvider] HTTP status: {response.status_code}")
                if response.status_code != 200:
                    if response.status_code == 400 and not response.text:
                        logger.error("Empty 400 response. Check model name and endpoint compatibility.")
                    logger.error(f"Request to {url} failed with status code {response.status_code}")
                    logger.error(f"Response text: {response.text}")
                    logger.error(f"Payload: {payload}")
                    logger.error(f"Request headers: {response.request.headers}")
                    logger.error(f"Request body: {response.request.content}")
                    raise httpx.HTTPStatusError(
                        f"Client error {response.status_code} - {response.text}",
                        request=response.request,
                        response=response,
                    )

                data = response.json()
                logger.debug(f"[AiFoundryProvider] Response JSON: {data}")

                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("No choices returned in response")

                choice = choices[0]
                message = choice.get("message") or choice.get("delta")
                logger.debug(f"[AiFoundryProvider] Choice extracted: {choice}")

                if not message:
                    logger.error(f"No message or delta found in choice: {choice}")
                    raise ValueError("No valid message content returned from model.")

                content = message.get("content", "")
                logger.debug(f"[AiFoundryProvider] Raw model content: {content}")

                if not isinstance(content, str) or not content.strip():
                    logger.error(f"[AiFoundryProvider] Invalid or empty content: {content}")
                    raise ValueError("Model response content must be a non-empty string.")

                return TextMessage.model_construct(
                    type="chat_message",
                    role="assistant",
                    content=content.strip(),
                    name="AiFoundryProvider",
                    source="ai-foundry"
                )
        except Exception as e:
            logger.exception(f"[AiFoundryProvider] Error during message creation: {type(e).__name__} - {str(e)}")
            raise