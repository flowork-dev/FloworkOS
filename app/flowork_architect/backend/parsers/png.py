########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\png.py total lines 26 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from .base import BaseParser

class PngParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.id = "png"
        self.color = "#b83b8e" # Ungu Media
        self.icon = "f1c5"     # Icon Image
        self.priority = 50

    def supports(self, file_name: str, ext: str) -> bool:
        return ext == "png"

    def parse(self, content: str, file_path: str) -> dict:
        return {
            "imports": [],
            "assets": [],
            "structure": [],
            "is_binary": True # Flag penting biar kernel gak error baca utf-8
        }
