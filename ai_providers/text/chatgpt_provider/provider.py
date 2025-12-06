########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\chatgpt_provider\provider.py total lines 65 
########################################################################

import os
try:
    from flowork_kernel.api_contract import BaseAIProvider
except ImportError:
    from ai_providers.BaseAIProvider import BaseAIProvider

from .core.ChatGPTConnection import ChatGPTConnection

class ChatGPTProvider(BaseAIProvider):

    def __init__(self, kernel, manifest: dict):
        super().__init__(kernel, manifest)
        self.connection = ChatGPTConnection(self.kernel)

    def get_provider_name(self) -> str:
        return self.loc.get("chatgpt_provider_name", fallback="OpenAI ChatGPT")

    def is_ready(self) -> tuple[bool, str]:
        if self.connection.configure():
            return (True, "")
        else:
            return (
                False,
                self.loc.get(
                    "chatgpt_provider_err_not_configured",
                    fallback="ChatGPT Provider is not configured. Check for a valid OPENAI_API_KEY in Settings.",
                ),
            )

    def generate_response(self, prompt: str, stream: bool = False, **kwargs) -> dict:
        is_ready, message = self.is_ready()
        if not is_ready:
            return {"type": "text", "data": f"ERROR: {message}"}

        messages = kwargs.get('messages', None)

        try:
            if stream:
                return self._stream_response(prompt, messages)
            else:
                response_dict = self.connection.get_chat_completion(prompt, messages=messages)
                if "error" in response_dict:
                    return {
                        "type": "text",
                        "data": self.loc.get("chatgpt_api_error", fallback="CHATGPT_API_ERROR: {error}", error=response_dict["error"]),
                    }
                else:
                    return {"type": "text", "data": response_dict["data"]}

        except Exception as e:
            return {"type": "text", "data": f"Critical Provider Error: {str(e)}"}

    def _stream_response(self, prompt, messages=None):
        if hasattr(self.connection, 'get_chat_stream'):
            iterator = self.connection.get_chat_stream(prompt, messages=messages)
            for chunk in iterator:
                yield chunk
        else:
            yield "[Streaming not supported]"
