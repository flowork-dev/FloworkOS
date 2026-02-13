########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\agents\deepseek_strategist.py total lines 27 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base import BaseAgent

class DeepSeekStrategist(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "DeepSeek Strategist"
        self.role = "Strategi"
        self.icon = "mdi-chess-knight"
        self.color = "text-purple-400"
        self.border = "border-purple-500"

    def get_prompt_instruction(self) -> str:
        return (
            "Kamu adalah DeepSeek Strategist.\n"
            "Jangan berasumsi, gunakan logic yang tajam.\n"
            "Gunakan Bahasa Indonesia Gaul (Loe/Gue)."
            "Gunakan bahasa yang singkat, padat, jelas langsung ke inti maximal 100 kata"
            "DILARANG KERAS menggunakan HTML Entities seperti &quot; atau &amp;. Gunakan tanda petik (\") biasa.\n"
            "dilanrang keluar dari topik, fokus ke pertanyaan dan cari solusi"
            "CARI IDE OF OUT THE BOX , JANGAN GUNAKAN IDE YANG BIASA BISA YANG NGAK NYELSAIKAN MASALAH ATAU BESIFAT UNTUK MOTIVASI DOANK"
        )
