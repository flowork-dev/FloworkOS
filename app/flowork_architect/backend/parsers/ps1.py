########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\ps1.py total lines 82 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class PowershellParser(BaseParser):
    """
    SPECIALIST PARSER FOR POWERSHELL SCRIPTS (.ps1, .psm1)
    Capabilities:
    1. Structure: Functions and Workflow blocks.
    2. Wiring: Detects Invoke-Expression, Dot-Sourcing, and file refs.
    3. Security: Scans for ConvertTo-SecureString usage (common weak point).
    """

    def __init__(self):
        super().__init__()
        self.color = "#5391FE"  # PowerShell Blue
        self.icon = "f120"      # Terminal Icon (Classic)
        self.priority = 80      # Medium Priority

    def supports(self, filename, ext):
        return ext in ["ps1", "psm1", "psd1"]

    def parse(self, content, path):
        imports = set()
        structure = []

        files_pattern = r'[\w\-\.\/]+\.(?:py|js|json|yml|yaml|bat|cmd|sh|ps1|txt|exe)'

        for match in re.findall(files_pattern, content):
            clean_name = match.split('/')[-1]
            clean_name = clean_name.replace('.\\', '') # Bersihkan .\ windows style
            current_filename = path.split('/')[-1]

            if clean_name.lower() != current_filename.lower():
                imports.add(clean_name)

        func_pattern = r'(?i)^[\s]*(?:function|filter|workflow)\s+([\w\-]+)'
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
            "Hardcoded Password": r'\$password\s*=\s*["\'].*["\']',
            "Secure String (Plain)": r'ConvertTo-SecureString\s+["\'].*["\']\s+-AsPlainText',
            "API Key": r'\$[\w]*Key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']'
        }
        for name, pattern in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                risks.append(f"Potential {name}")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks

        todos = len(re.findall(r'#.*?(TODO|FIXME)', content, re.IGNORECASE))
        if todos > 0: metrics['todo_count'] = todos

        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
