########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\gemini_provider\core\GeminiConnection.py total lines 67 
########################################################################

import google.generativeai as genai
import os
import time

class GeminiConnection:
    def __init__(self, kernel):
        self.kernel = kernel
        self.api_key = None
        self._last_retry = 0 # [GEMINI ADDED] Prevent spamming DB

    def configure(self, user_id=None):
        """
        Konfigurasi menggunakan API Key dari Database Flowork.
        """
        self.api_key = self.kernel.variable_manager.get_variable("GEMINI_API_KEY", user_id=user_id)

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                return True
            except Exception as e:
                self.kernel.write_to_log(f"[GeminiConnection] Config Error: {e}", "ERROR")
                return False
        else:
            return False

    def get_model(self, model_name):
        if not self.api_key:
            self.configure()

        if not self.api_key:
            raise Exception("Gemini API Key not configured. Set GEMINI_API_KEY in Variables.")

        genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(model_name)

    def list_available_models(self):
        """
        [GEMINI REFACTOR] Robust discovery. Tries to configure itself before returning 0.
        """
        if not self.api_key:
            self.configure()

        if not self.api_key:
            return []

        try:
            genai.configure(api_key=self.api_key)
            all_models = list(genai.list_models())
            text_models = []
            for m in all_models:
                if 'generateContent' in m.supported_generation_methods:
                    text_models.append(m.name)

            if text_models:
                self.kernel.write_to_log(f"[Gemini] Discovered {len(text_models)} API models.", "SUCCESS")

            return text_models
        except Exception as e:
            self.kernel.write_to_log(f"[GeminiConnection] List Models Failed: {e}", "WARNING")
            return []
