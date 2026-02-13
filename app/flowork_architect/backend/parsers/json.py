########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\json.py total lines 93 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
import json
from .base import BaseParser

class JsonParser(BaseParser):
    """
    SPECIALIST PARSER FOR JSON FILES (.json)
    Capabilities:
    1. Structural Analysis (Top-level keys).
    2. Universal Reference Scanning (Finds file paths in values).
    3. Security Scanning for credentials in config files.
    """

    def __init__(self):
        super().__init__()
        self.color = "#F1E05A"  # JavaScript/JSON Yellow
        self.icon = "f1c0"      # File Code Icon
        self.priority = 90      # High Priority (Config files drive logic)

    def supports(self, filename, ext):
        return ext == "json"

    def parse(self, content, path):
        imports = set()
        structure = []

        files_pattern = r'["\'][\w\-\.\/]+\.(?:py|js|json|yml|yaml|txt|bat|cmd|sh|ps1|env|ini|vue|css|html|png|jpg|svg)["\']'

        for match in re.findall(files_pattern, content):
            clean_name = match.strip('"\'').split('/')[-1]

            current_filename = path.split('/')[-1]
            if clean_name.lower() != current_filename.lower():
                imports.add(clean_name)

        try:
            data = json.loads(content)
            if isinstance(data, dict):
                for key in data.keys():
                    structure.append({
                        "name": key,
                        "type": "key",
                        "icon": "fa-key"
                    })
            elif isinstance(data, list):
                structure.append({
                    "name": f"Array[{len(data)}]",
                    "type": "list",
                    "icon": "fa-list"
                })
        except:
            structure.append({"name": "Invalid JSON", "type": "error", "icon": "fa-triangle-exclamation"})

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "assets": [],
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        """
        Scans values for potential secrets.
        """
        risks = []
        patterns = {
            "API Key": r'(?i)"[\w_]*(?:api|secret)_?key"\s*:\s*"\s*([a-zA-Z0-9_\-]{20,})\s*"',
            "Token": r'(?i)"[\w_]*token"\s*:\s*"\s*([a-zA-Z0-9_\-]{20,})\s*"',
        }

        for name, pattern in patterns.items():
            if re.search(pattern, content):
                risks.append(f"Potential {name} in config")

        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks

        todo_keys = len(re.findall(r'"_?todo"', content, re.IGNORECASE))
        metrics['todo_count'] = todo_keys

        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
