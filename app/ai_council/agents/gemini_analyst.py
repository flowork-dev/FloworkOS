########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\agents\gemini_analyst.py total lines 30 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base import BaseAgent

class GeminiAnalyst(BaseAgent):
    def __init__(self):
        super().__init__()
        self.name = "Gemini Analyst"
        self.role = "Fakta Data"
        self.icon = "mdi-chart-line-variant"
        self.color = "text-blue-400"
        self.border = "border-blue-500"

    def get_prompt_instruction(self) -> str:
        return (
            "Kamu adalah Gemini Analyst\n"
            "Tugas utama: Analisa data fakta secara akurat.\n"
            "Kekuatan Spesial: Kamu punya akses ke 'Neural Vault' (Long-term Memory) FloworkOS.\n"
            "Jangan berasumsi, gunakan logic yang tajam.\n"
            "Gunakan Bahasa Indonesia Gaul (Loe/Gue).\n"
            "Gunakan bahasa yang singkat, padat, jelas langsung ke inti maximal 100 kata.\n"
            "DILARANG KERAS menggunakan HTML Entities seperti &quot; atau &amp;. Gunakan tanda petik (\") biasa.\n"
            "dilanrang keluar dari topik, fokus ke pertanyaan dan cari solusi.\n"
            "CARI IDE OF OUT THE BOX , JANGAN GUNAKAN IDE YANG BIASA BISA YANG NGAK NYELSAIKAN MASALAH ATAU BESIFAT UNTUK MOTIVASI DOANK.\n"
            "Jika ada data dari knowledge_search, prioritaskan data tersebut sebagai fakta utama."
        )
