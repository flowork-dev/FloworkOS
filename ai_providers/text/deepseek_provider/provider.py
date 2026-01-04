########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\deepseek_provider\provider.py total lines 63 
########################################################################

import os
try:
    from flowork_kernel.api_contract import BaseAIProvider
except ImportError:
    from ai_providers.BaseAIProvider import BaseAIProvider

from .core.DeepSeekConnection import DeepSeekConnection

class DeepSeekProvider(BaseAIProvider):

    def __init__(self, kernel, manifest: dict):
        super().__init__(kernel, manifest)
        self.connection = DeepSeekConnection(self.kernel)

    def get_provider_name(self) -> str:
        return self.loc.get("deepseek_provider_name", fallback="DeepSeek AI")

    def is_ready(self, user_id=None, **kwargs) -> tuple[bool, str]:
        uid = user_id or kwargs.get('user_id')
        if self.connection.configure(user_id=uid):
            return (True, "")
        else:
            return (False, "DeepSeek API Key not found. Please set DEEPSEEK_API_KEY in Settings.")

    def generate_response(self, prompt: str, **kwargs) -> dict:
        user_id = kwargs.get('user_id')
        is_ready, message = self.is_ready(user_id=user_id)
        if not is_ready:
            return {"type": "text", "data": f"ERROR: {message}"}

        target_model = kwargs.get('model', "deepseek-chat")

        try:
            self.kernel.write_to_log(f"[DeepSeek] Querying model: {target_model}...", "INFO")
            response_dict = self.connection.get_chat_completion(
                prompt,
                model=target_model,
                messages=kwargs.get('messages')
            )

            if "error" in response_dict:
                alt_model = "deepseek-reasoner" if target_model == "deepseek-chat" else "deepseek-chat"
                self.kernel.write_to_log(f"[DeepSeek] Model {target_model} failed. Trying {alt_model}...", "WARNING")

                response_dict = self.connection.get_chat_completion(
                    prompt,
                    model=alt_model,
                    messages=kwargs.get('messages')
                )

            if "error" in response_dict:
                return {"type": "text", "data": f"DEEPSEEK_API_ERROR: {response_dict['error']}"}

            return {"type": "text", "data": response_dict["data"]}

        except Exception as e:
            return {"type": "text", "data": f"Critical DeepSeek Provider Error: {str(e)}"}
