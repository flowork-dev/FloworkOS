########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\js.py total lines 101 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class JavascriptParser(BaseParser):
    """
    SPECIALIST PARSER FOR JAVASCRIPT FILES (.js, .jsx, .mjs)
    Capabilities:
    1. Detects ES6 Imports (import ... from ...).
    2. Detects CommonJS (require(...)).
    3. Universal Reference Scanning (Strings pointing to files).
    4. Structure Analysis (Functions, Classes, Consts).
    5. Security Scanning (Secrets).
    """

    def __init__(self):
        super().__init__()
        self.color = "#F7DF1E"  # JS Yellow
        self.icon = "f3b9"      # JS Brand Icon
        self.priority = 95      # Very High Priority

    def supports(self, filename, ext):
        return ext in ["js", "jsx", "mjs", "cjs"]

    def parse(self, content, path):
        imports = set()
        assets = set()
        structure = []

        es6_pattern = r'import\s+(?:[\w\s{},*]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.findall(es6_pattern, content):
            clean = match.split('/')[-1]
            imports.add(clean)

        cjs_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for match in re.findall(cjs_pattern, content):
            clean = match.split('/')[-1]
            imports.add(clean)

        files_pattern = r'[\w\-\.\/]+\.(?:py|js|json|yml|yaml|svg|png|jpg|css|vue|html)'
        for match in re.findall(files_pattern, content):
            clean_name = match.split('/')[-1]
            current_filename = path.split('/')[-1]

            if clean_name != current_filename and clean_name not in imports:
                imports.add(clean_name)

        func_pattern = r'(?:async\s+)?function\s+([\w\$]+)\s*\('
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(func_pattern, line)
            if match:
                structure.append({"name": match.group(1), "type": "function", "line": line_num, "icon": "fa-code"})

        class_pattern = r'class\s+([\w\$]+)'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(class_pattern, line)
            if match:
                structure.append({"name": match.group(1), "type": "class", "line": line_num, "icon": "fa-cube"})

        const_pattern = r'export\s+const\s+([\w\$]+)'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(const_pattern, line)
            if match:
                structure.append({"name": match.group(1), "type": "const", "line": line_num, "icon": "fa-cube"})

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "assets": list(assets),
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        risks = []
        patterns = {
            "API Key": r"(?i)(apiKey|secretKey|accessToken)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            "Hardcoded Auth": r"Authorization:\s*['\"]Bearer\s+[a-zA-Z0-9\-\._]+['\"]"
        }

        for name, pattern in patterns.items():
            if re.search(pattern, content):
                risks.append(f"Potential {name}")

        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks

        todos = len(re.findall(r'(?://|/\*).*?(TODO|FIXME|DANGER)', content, re.IGNORECASE | re.DOTALL))
        if todos > 0: metrics['todo_count'] = todos

        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
