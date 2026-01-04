########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\png.py total lines 26 
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
