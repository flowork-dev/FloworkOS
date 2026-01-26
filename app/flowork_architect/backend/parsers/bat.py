########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\bat.py total lines 81 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class BatchParser(BaseParser):
    """
    SPECIALIST PARSER FOR WINDOWS BATCH FILES (.bat, .cmd)
    Capabilities:
    1. Universal Asset Detection (Finds .py, .yml, .json, .txt refs).
    2. Identifies Labels as structure.
    3. Security Scanning for secrets.
    """

    def __init__(self):
        super().__init__()
        self.color = "#C1F12E"  # Lime Terminal Color
        self.icon = "f17a"      # Windows Icon
        self.priority = 80      # Medium Priority

    def supports(self, filename, ext):
        return ext in ["bat", "cmd"]

    def parse(self, content, path):
        imports = set()
        assets = set()
        structure = []

        files_pattern = r'[\w\-\.\/\\]+\.(?:py|js|json|yml|yaml|txt|bat|cmd|sh|ps1|env|ini)'

        for match in re.findall(files_pattern, content):
            clean_name = match.replace('\\', '/').split('/')[-1]

            current_filename = path.split('/')[-1]
            if clean_name.lower() != current_filename.lower():
                imports.add(clean_name)

        label_pattern = r'^\s*:([\w\-]+)'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(label_pattern, line)
            if match:
                structure.append({
                    "name": match.group(1),
                    "type": "label",
                    "line": line_num,
                    "icon": "fa-tag"
                })

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports), # Ini kunci agar Inbound/Outbound muncul
            "assets": list(assets),
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        risks = []
        patterns = {
            "Hardcoded Password": r'(?i)set\s+["\']?password["\']?\s*=',
            "API Key Assignment": r'(?i)set\s+["\']?api_key["\']?\s*=',
            "AWS Secret": r'aws_secret_access_key',
        }
        for name, pattern in patterns.items():
            if re.search(pattern, content): risks.append(f"Potential {name}")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks

        rem_todos = len(re.findall(r'(?:REM|::).*?(TODO|FIXME|DANGER)', content, re.IGNORECASE))
        if rem_todos > 0: metrics['todo_count'] = rem_todos

        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
