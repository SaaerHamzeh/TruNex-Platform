from llama_index.core.llms.llm import LLM
from llama_index.core.llms import ChatMessage, LLMMetadata
from typing import List
import requests
from llama_index.core.llms import ChatMessage, ChatResponse
from llama_index.core.settings import Settings  



class OpenRouterLLM(LLM):
    def __init__(self, model: str, api_key: str):
        super().__init__()
        self._model = model
        self._api_key = api_key
        self._api_url = "https://openrouter.ai/api/v1/chat/completions"

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=8000,
            num_output=1000,
            is_chat_model=True,
            model_name=self._model,
        )

    def chat(self, messages: List[ChatMessage], **kwargs) -> ChatResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "TruNex Text-to-SQL",
        }

        messages_payload = [{"role": "system", "content": Settings.system_prompt}] + [
            {"role": m.role.value, "content": m.content} for m in messages
        ]

        payload = {
            "model": self._model,
            "messages": messages_payload,
            "temperature": 0.2,
            "max_tokens": kwargs.get("max_tokens", 1000),
        }
        # print("🧠 Messages to LLM:", messages_payload)

        response = requests.post(self._api_url, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # ✅ رجّع ChatResponse بدلاً من str
        return ChatResponse(message=ChatMessage(role="assistant", content=content))

    def complete(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("Completion غير مدعوم")

    def stream_chat(self, messages: List[ChatMessage], **kwargs):
        raise NotImplementedError("stream_chat غير مدعوم")

    def stream_complete(self, prompt: str, **kwargs):
        raise NotImplementedError("stream_complete غير مدعوم")

    async def achat(self, messages: List[ChatMessage], **kwargs):
        raise NotImplementedError("achat غير مدعوم")

    async def acomplete(self, prompt: str, **kwargs):
        raise NotImplementedError("acomplete غير مدعوم")

    async def astream_chat(self, messages: List[ChatMessage], **kwargs):
        raise NotImplementedError("astream_chat غير مدعوم")

    async def astream_complete(self, prompt: str, **kwargs):
        raise NotImplementedError("astream_complete غير مدعوم")
