########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\config.py total lines 72 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class ConfigParser(BaseParser):
    """
    SPECIALIST PARSER FOR STRUCTURED CONFIGS (.toml, .xml, .conf, .webmanifest)
    Capabilities:
    1. Structure: XML Tags, TOML Sections, CONF keys.
    2. Universal Wiring: Finds file paths.
    """

    def __init__(self):
        super().__init__()
        self.color = "#00BCD4"  # Cyan
        self.icon = "f013"      # Cog Icon
        self.priority = 85

    def supports(self, filename, ext):
        return ext in ["toml", "xml", "conf", "webmanifest", "on", "awenkaudico", "scss"]

    def parse(self, content, path):
        imports = set()
        structure = []

        files_pattern = r'[\w\-\.\/]+\.(?:py|js|json|yml|yaml|css|html|txt|png|jpg|svg)'
        for match in re.findall(files_pattern, content):
            clean = match.split('/')[-1]
            if clean.lower() != path.split('/')[-1].lower():
                imports.add(clean)


        for line_num, line in enumerate(content.splitlines(), 1):
            if re.search(r'^\[.*\]', line):
                structure.append({"name": line.strip(), "type": "section", "line": line_num, "icon": "fa-square"})

        if "xml" in path or "manifest" in path:
            tags = re.findall(r'<([\w\-]+)', content)
            for tag in list(set(tags))[:10]:
                structure.append({"name": f"<{tag}>", "type": "tag", "icon": "fa-code"})

        if "conf" in path or "SET" in path:
            for line_num, line in enumerate(content.splitlines(), 1):
                if "=" in line and not line.startswith("#"):
                    key = line.split("=")[0].strip()
                    structure.append({"name": key, "type": "key", "line": line_num, "icon": "fa-key"})

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "assets": [],
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        risks = []
        if re.search(r'(?i)(password|secret|key)\s*=', content):
            risks.append("Potential Secret")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks
        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
