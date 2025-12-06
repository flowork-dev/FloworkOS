########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\chatgpt_provider\core\ChatGPTConnection.py total lines 95 
########################################################################

import os
import requests
import json

class ChatGPTConnection:
    def __init__(self, kernel):
        self.kernel = kernel
        self.api_key = None
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def configure(self):
        self.api_key = self.kernel.variable_manager.get_variable("OPENAI_API_KEY")

        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            self.kernel.write_to_log("[ChatGPTConnection] API Key not found in DB or Env.", "WARNING")
            return False

        return True

    def get_chat_completion(self, prompt, messages=None, model="gpt-4o"):
        if not self.api_key:
            return {"error": "Missing API Key"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload_messages = []
        if messages:
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                if content:
                    payload_messages.append({"role": role, "content": content})

        if not payload_messages or payload_messages[-1]["content"] != prompt:
            payload_messages.append({"role": "user", "content": prompt})

        data = {
            "model": model,
            "messages": payload_messages
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return {"data": content}
        except Exception as e:
            return {"error": str(e)}

    def get_chat_stream(self, prompt, messages=None, model="gpt-4o"):
        if not self.api_key:
            yield "Error: Missing API Key"
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload_messages = []
        if messages:
            for m in messages:
                payload_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        payload_messages.append({"role": "user", "content": prompt})

        data = { "model": model, "messages": payload_messages, "stream": True }

        try:
            with requests.post(self.api_url, headers=headers, json=data, stream=True, timeout=60) as r:
                for line in r.iter_lines():
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: ') and line_str != 'data: [DONE]':
                            try:
                                json_str = line_str[6:]
                                chunk = json.loads(json_str)
                                delta = chunk['choices'][0]['delta']
                                if 'content' in delta:
                                    yield delta['content']
                            except: pass
        except Exception as e:
            yield f"[Stream Error: {e}]"
