########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\media.py total lines 65 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class MediaParser(BaseParser):
    """
    SPECIALIST PARSER FOR BINARY ASSETS & AI MODELS
    Covers: Images, Vectors, Executables, AI Models, Archives, AND DATABASES (Safe Mode).
    """

    def __init__(self):
        super().__init__()
        self.color = "#C839C5"  # Vibrant Media Purple/Pink
        self.icon = "f1c5"      # File Image Icon
        self.priority = 60

    def supports(self, filename, ext):
        return ext in [
            "svg", "png", "jpg", "jpeg", "gif", "webp", "ico",
            "safetensors", "gguf", "bin", "pt", "pth", "ckpt",
            "pdf", "docx", "xlsx", "zip", "rar", "7z", "tar", "gz",
            "exe", "dll", "so", "msi",
            "sql", "db", "sqlite", "sqlite3", "db-shm", "db-wal", "mdb"
        ]

    def parse(self, content, path):
        imports = set()
        structure = []
        metrics = {"loc": 0, "complexity": "LOW", "todo_count": 0}

        ext = path.split('.')[-1].lower()

        if ext == "svg":
            metrics = self.analyze_vital_signs(content)
            id_pattern = r'<(?:g|path|rect|circle|polygon).*?id=["\']([^"\']+)["\']'
            for line_num, line in enumerate(content.splitlines(), 1):
                match = re.search(id_pattern, line)
                if match:
                    structure.append({"name": f"#{match.group(1)}", "type": "vector-id", "line": line_num, "icon": "fa-vector-square"})

        elif ext in ["safetensors", "gguf", "bin", "pt", "db", "sqlite", "sql"]:
            metrics["complexity"] = "ASSET"
            structure.append({"name": "Binary/Data Asset", "type": "binary", "icon": "fa-database"})

        else:
            metrics["complexity"] = "ASSET"

        return {
            "imports": list(imports),
            "assets": [],
            "structure": structure,
            "metrics": metrics
        }

    def analyze_vital_signs(self, content, security_risks=None):
        try:
            loc = len(content.splitlines())
            return {"loc": loc, "complexity": "LOW", "todo_count": 0}
        except:
            return {"loc": 0, "complexity": "ASSET", "todo_count": 0}
