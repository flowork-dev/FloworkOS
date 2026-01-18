########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\yaml.py total lines 52 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class YamlParser(BaseParser):
    """
    SPECIALIST PARSER FOR YAML FILES (.yml)
    """

    def __init__(self):
        super().__init__()
        self.color = "#CB171E"
        self.icon = "f813"
        self.priority = 85

    def supports(self, filename, ext):
        return ext in ["yml", "yaml"]

    def parse(self, content, path):
        imports = set()
        structure = []

        files_pattern = r'[\w\-\.\/]+\.(?:dockerfile|env|json|py|sh|txt|conf|ini)'
        for match in re.findall(files_pattern, content):
            clean = match.split('/')[-1]
            if clean.lower() != path.split('/')[-1].lower():
                imports.add(clean)

        if "Dockerfile" in content: imports.add("Dockerfile")

        key_pattern = r'^([\w\-]+):'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(key_pattern, line)
            if match:
                structure.append({
                    "name": match.group(1),
                    "type": "key",
                    "line": line_num,
                    "icon": "fa-cube"
                })

        return {
            "imports": list(imports),
            "assets": [],
            "structure": structure,
            "metrics": super().analyze_vital_signs(content)
        }
