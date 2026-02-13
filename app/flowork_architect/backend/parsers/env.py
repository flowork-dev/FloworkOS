########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\env.py total lines 81 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class EnvParser(BaseParser):
    """
    SPECIALIST PARSER FOR .ENV FILES
    Capabilities:
    1. Structure: Lists all Configuration Keys.
    2. Wiring: Detects file paths inside variable values.
    3. Security: High-level audit for exposed secrets.
    """

    def __init__(self):
        super().__init__()
        self.color = "#009688"  # Teal / Config Color
        self.icon = "f013"      # Gear/Cog Icon
        self.priority = 95      # Very High (Critical Config)

    def supports(self, filename, ext):
        return filename.startswith(".env") or ext == "env" or filename == "config"

    def parse(self, content, path):
        imports = set()
        structure = []

        files_pattern = r'[\w\-\.\/]+\.(?:py|js|json|yml|yaml|bat|cmd|sh|db|sqlite|pem|crt|key|txt|log)'

        for match in re.findall(files_pattern, content):
            clean_name = match.split('/')[-1]
            current_filename = path.split('/')[-1]
            if clean_name.lower() != current_filename.lower():
                imports.add(clean_name)

        key_pattern = r'^(?:export\s+)?([A-Z0-9_]+)\s*='

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'): continue

            match = re.search(key_pattern, line)
            if match:
                key_name = match.group(1)
                structure.append({
                    "name": key_name,
                    "type": "key",
                    "line": line_num,
                    "icon": "fa-key"
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
        if re.search(r'(?i)DEBUG\s*=\s*True', content):
            risks.append("Debug Mode Enabled (Risk)")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks

        todos = len(re.findall(r'#.*?(TODO|FIXME)', content, re.IGNORECASE))
        if todos > 0: metrics['todo_count'] = todos

        if metrics['loc'] > 100: metrics['complexity'] = "HIGH"

        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
