import httpx
import json
import asyncio

class FoundryResponse:
    def __init__(self, content, ledger_info=None):
        self.content = content
        self.ledger_info = ledger_info or {}

class FoundryLocalClient:
    def __init__(self, base_url, model):
        self.base_url = base_url
        self.model = model

    @property
    def model_info(self):
        # Define your model's capabilities
        return {
            "function_calling": True,
            "vision": False
        }

    async def create(self, messages, cancellation_token=None, json_output=False):
        formatted_messages = []
        for m in messages:
            if isinstance(m, dict):
                role = m.get("role", "user")
                content = m.get("content", "")
            else:
                role = getattr(m, "role", "user")
                content = getattr(m, "content", "")
            if content:
                formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.7,
            "max_tokens": 1024,
            "json_output": json_output
        }

        print("DEBUG Foundry Payload:")
        print(json.dumps(payload, indent=2))

        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
            for attempt in range(3):
                try:
                    resp = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
                    resp.raise_for_status()
                    data = resp.json()

                    # Ensure model response includes ledger_info at top level if missing
                    if 'choices' in data and isinstance(data['choices'], list) and data['choices']:
                        message_obj = data['choices'][0].get('message', {})
                        if 'ledger_info' not in message_obj or not isinstance(message_obj['ledger_info'], dict):
                            print("WARNING: Model response missing ledger_info, requesting model to regenerate.")
                            # Optionally add a regeneration logic here, for now raise a clean error
                            raise ValueError("Model response did not contain valid ledger_info. Aborting orchestration.")
                    else:
                        print("ERROR: No choices returned in response.")
                        raise ValueError("Model response did not contain choices. Aborting orchestration.")

                    # Extract assistant message
                    choices = data.get("choices", [])

                    if choices:
                        message_obj = choices[0].get("message", {})
                        assistant_message = message_obj.get("content", "")
                        ledger_info = message_obj.get("ledger_info")
                        if ledger_info is None:
                            ledger_info = {}
                            print(f"INFO: ledger_info not available in response (attempt {attempt + 1}). Proceeding without ledger_info.")

                    else:
                        assistant_message = ""
                        ledger_info = {}
                        print(f"INFO: No choices returned in response (attempt {attempt + 1}).")

                    # Removed fallback injection logic as per instructions

                    return FoundryResponse(content=assistant_message, ledger_info=ledger_info)

                except httpx.ReadTimeout:
                    print(f"WARNING: Timeout on attempt {attempt + 1}")
                    if attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        return FoundryResponse(content="Timeout occurred. Please try again later.")
                except httpx.HTTPStatusError as exc:
                    print(f"HTTP error: {exc}")
                    return FoundryResponse(content=f"HTTP error {exc.response.status_code}")
                except Exception as exc:
                    print(f"Unexpected error: {exc}")
                    raise

class FoundryLocalProvider:
    def __init__(self):
        self.base_url = "http://localhost:5273"

    def get_client(self, model):
        return FoundryLocalClient(base_url=self.base_url, model=model)