########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\gemini_provider\provider.py total lines 90 
########################################################################

import os
import time
try:
    from flowork_kernel.api_contract import BaseAIProvider
except ImportError:
    from ai_providers.BaseAIProvider import BaseAIProvider

from .core.GeminiConnection import GeminiConnection

class GeminiProvider(BaseAIProvider):
    TIER = "basic"

    def __init__(self, kernel, manifest: dict):
        super().__init__(kernel, manifest)
        self.connection = GeminiConnection(self.kernel)

    def get_provider_name(self) -> str:
        return self.loc.get("gemini_provider_name", fallback="Google Gemini")

    def is_ready(self, user_id=None, **kwargs) -> tuple[bool, str]:
        uid = user_id or kwargs.get('user_id')
        if self.connection.configure(user_id=uid):
            return (True, "")
        return (False, "Gemini Provider not configured. Check Settings.")

    def generate_response(self, prompt: str, **kwargs) -> dict:
        user_id = kwargs.get('user_id')
        is_ready, message = self.is_ready(user_id=user_id)
        if not is_ready:
            return {"type": "text", "data": f"ERROR: {message}"}

        available_models = self.connection.list_available_models()

        primary_candidates = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]

        target_model = None
        if available_models:
            for p in primary_candidates:
                for avail in available_models:
                    if p in avail:
                        target_model = avail; break
                if target_model: break

        if not target_model: target_model = "gemini-1.5-flash"

        try:
            return self._try_generate(target_model, prompt)
        except Exception as e:
            err = str(e)

            if "429" in err or "404" in err or "quota" in err.lower() or "not found" in err.lower():
                self.kernel.write_to_log(f"[Gemini] Primary {target_model} failed. Initiating Fallback Chain...", "WARNING")

                fallback_chain = [
                    "gemini-1.5-flash",        # Standard alias
                    "gemini-1.5-flash-latest", # Latest alias
                    "gemini-1.5-pro",          # Pro tier
                    "gemini-pro"               # Legacy
                ]

                for fallback_model in fallback_chain:
                    if fallback_model in target_model: continue

                    try:
                        self.kernel.write_to_log(f"[Gemini] Trying fallback: {fallback_model}...", "INFO")
                        if "429" in err: time.sleep(1)
                        return self._try_generate(fallback_model, prompt)
                    except Exception: continue

            return {"type": "text", "data": f"GEMINI_API_ERROR (All Models Failed). Last Error: {err}"}

    def _try_generate(self, model_name, prompt):
        clean_name = model_name.replace("models/", "")

        model = self.connection.get_model(clean_name)
        response = model.generate_content(prompt)

        if not response.text and response.prompt_feedback:
            return {"type": "text", "data": f"Blocked: {response.prompt_feedback}"}
        return {"type": "text", "data": response.text}
