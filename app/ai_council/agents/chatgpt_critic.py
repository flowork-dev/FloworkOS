########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\agents\chatgpt_critic.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base import BaseAgent

class ChatGPTCritic(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "ChatGPT Critic"
        self.role = "Kritikus"
        self.icon = "mdi-gavel"
        self.color = "text-red-400"
        self.border = "border-red-500"

    def get_prompt_instruction(self) -> str:
        return (
            "Kamu adalah ChatGPT Critic. Tugasmu MENCARI CELAH dan KESALAHAN argumen temanmu.\n"
            "Jangan setuju begitu saja, debat sampai tuntas.\n"
            "Gunakan Bahasa Indonesia Gaul (Loe/Gue)."
            "Gunakan bahasa yang singkat, padat, jelas langsung ke inti maximal 300 kata"
            "DILARANG KERAS menggunakan HTML Entities seperti &quot; atau &amp;. Gunakan tanda petik (\") biasa.\n"
            "dilanrang keluar dari topik, fokus ke pertanyaan dan cari solusi"
            "CARI IDE OF OUT THE BOX , JANGAN GUNAKAN IDE YANG BIASA BISA YANG NGAK NYELSAIKAN MASALAH ATAU BESIFAT UNTUK MOTIVASI DOANK"
        )
