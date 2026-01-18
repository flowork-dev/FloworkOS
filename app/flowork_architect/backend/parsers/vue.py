########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\vue.py total lines 86 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class VueParser(BaseParser):
    """
    SPECIALIST PARSER FOR VUE/HTML FILES
    Capabilities:
    1. Regex extraction for Template, Script, and Style sections.
    2. Import and Asset detection.
    3. Security Scanning (Secret Hunter) in scripts.
    """

    def __init__(self):
        super().__init__()
        self.color = "#41B883" # Vue Green
        self.icon = "f41b"     # Vue Icon
        self.priority = 90     # Priority for Frontend files

    def supports(self, filename, ext):
        return ext in ["vue", "html"]

    def parse(self, content, path):
        imports = set()
        assets = set()
        structure = []

        import_pattern = r'import\s+(?:[\w\s{},*]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.findall(import_pattern, content):
            imports.add(match)

        asset_pattern = r'src=["\']([^"\']+)["\']'
        for match in re.findall(asset_pattern, content):
            if not match.startswith("http"): assets.add(match)

        if "<template>" in content:
            structure.append({"name": "Template", "type": "ui", "line": content.find("<template>") + 1, "icon": "fa-window-maximize"})
        if "<script>" in content:
            structure.append({"name": "Script", "type": "logic", "line": content.find("<script>") + 1, "icon": "fa-code"})
        if "<style>" in content:
            structure.append({"name": "Style", "type": "css", "line": content.find("<style>") + 1, "icon": "fa-paint-brush"})

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "assets": list(assets),
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        """
        THE SECRET HUNTER
        Scans for potential hardcoded secrets in JS code blocks.
        """
        risks = []
        patterns = {
            "API Key": r"(?i)(apiKey|secretKey|accessToken)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            "Hardcoded URL with Creds": r"https?://[^:]+:[^@]+@"
        }

        for name, pattern in patterns.items():
            if re.search(pattern, content):
                risks.append(f"Potential {name} detected")

        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)

        metrics['security_risks'] = security_risks

        html_todos = len(re.findall(r'', content, re.DOTALL))
        if html_todos > 0:
            metrics['todo_count'] += html_todos

        if len(security_risks) > 0:
            metrics['complexity'] = "CRITICAL"

        return metrics
