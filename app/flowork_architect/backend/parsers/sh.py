########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\sh.py total lines 75 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class ShellParser(BaseParser):
    """
    SPECIALIST PARSER FOR LINUX SHELL SCRIPTS (.sh, .bash)
    Capabilities:
    1. Universal Asset Detection (Finds .py, .yml, .json, .txt refs).
    2. Identifies Functions.
    3. Security Scanning.
    """

    def __init__(self):
        super().__init__()
        self.color = "#4EAA25"  # Bash Green
        self.icon = "f120"      # Terminal Icon
        self.priority = 80      # Medium Priority

    def supports(self, filename, ext):
        return ext in ["sh", "bash", "zsh"]

    def parse(self, content, path):
        imports = set()
        structure = []

        files_pattern = r'[\w\-\.\/]+\.(?:py|js|json|yml|yaml|txt|bat|cmd|sh|ps1|env|ini)'

        for match in re.findall(files_pattern, content):
            clean_name = match.split('/')[-1]
            current_filename = path.split('/')[-1]

            if clean_name != current_filename:
                imports.add(clean_name)

        func_pattern = r'^\s*(?:function\s+)?([\w\-]+)\s*\(\)'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(func_pattern, line)
            if match:
                structure.append({
                    "name": match.group(1),
                    "type": "function",
                    "line": line_num,
                    "icon": "fa-terminal"
                })

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "assets": [],
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        risks = []
        patterns = {
            "Exported Token": r'(?i)export\s+[\w_]*TOKEN[\w_]*\s*=',
            "Hardcoded Password": r'(?i)password\s*=',
        }
        for name, pattern in patterns.items():
            if re.search(pattern, content): risks.append(f"Potential {name}")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks
        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
