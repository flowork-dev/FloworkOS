########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\text\gemini_provider\core\GeminiChatSession.py total lines 23 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import google.generativeai as genai
class GeminiChatSession:

    def __init__(self, model_name="gemini-pro"):
        self.model = genai.GenerativeModel(model_name)
        self.chat_session = self.model.start_chat(history=[])
    def send_message(self, prompt: str) -> str:

        try:
            response = self.chat_session.send_message(prompt)
            return response.text
        except Exception as e:
            return f"Error during chat: {e}"
    @property
    def history(self):

        return self.chat_session.history
