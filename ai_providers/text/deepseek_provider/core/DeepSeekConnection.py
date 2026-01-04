########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\deepseek_provider\core\DeepSeekConnection.py total lines 64 
########################################################################

import requests
import json

class DeepSeekConnection:
    def __init__(self, kernel):
        self.kernel = kernel
        self.api_key = None
        self.base_url = "https://api.deepseek.com"

    def configure(self, user_id=None):
        """Ambil API Key dari variable manager FLOWORK"""
        self.api_key = self.kernel.variable_manager.get_variable("DEEPSEEK_API_KEY", user_id=user_id)
        if not self.api_key:
            self.kernel.write_to_log("[DeepSeekConnection] DEEPSEEK_API_KEY missing in Database.", "WARNING")
            return False
        return True

    def get_chat_completion(self, prompt, model="deepseek-chat", messages=None, **kwargs):
        """Execute chat request to DeepSeek"""
        if not self.api_key:
            return {"error": "Not configured"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        history = messages if messages else []
        if not history:
            history = [{"role": "user", "content": prompt}]

        payload = {
            "model": model,
            "messages": history,
            "stream": False,
            "temperature": kwargs.get("temperature", 0.7)
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return {"data": result['choices'][0]['message']['content']}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    def list_available_models(self):
        """DeepSeek standard model list"""
        return ["deepseek-chat", "deepseek-reasoner"]
