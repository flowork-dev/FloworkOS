########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\txt.py total lines 75 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class TextParser(BaseParser):
    """
    SPECIALIST PARSER FOR TEXT & DOCUMENTATION
    Covers: txt, md, log, ignore, csv, licenses.
    """

    def __init__(self):
        super().__init__()
        self.color = "#9E9E9E"  # Neutral Grey
        self.icon = "f15c"      # File Alt Icon
        self.priority = 50

    def supports(self, filename, ext):
        is_specific = filename in ["LICENSE", "Makefile", "Dockerfile"]
        return is_specific or ext in [
            "txt", "md", "log", "ini", "csv", "tsv",
            "gitignore", "dockerignore", "gitattributes",
            "installed", "requirements_hash", "vendor_hash"
        ]

    def parse(self, content, path):
        imports = set()
        assets = set()
        structure = []
        filename = path.split('/')[-1].lower()

        if "requirements" in filename:
            for line in content.splitlines():
                pkg_match = re.match(r'^([a-zA-Z0-9\-_]+)', line.strip())
                if pkg_match and not line.strip().startswith('#'):
                    assets.add(pkg_match.group(1))

        files_pattern = r'[\w\-\.\/]+\.(?:py|js|json|yml|yaml|bat|cmd|sh|vue|css|html|txt|png|jpg|whl)'
        for match in re.findall(files_pattern, content):
            clean = match.split('/')[-1]
            if clean.lower() != filename: imports.add(clean)

        header_pattern = r'^(?:#+|\[|=|--+)\s*(.*?)\s*(?:\]|=|--+)?$'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(header_pattern, line.strip())
            if match:
                name = match.group(1).strip()
                if name and len(name) > 2 and not name.startswith('='):
                    structure.append({"name": name[:40], "type": "section", "line": line_num, "icon": "fa-heading"})

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "assets": list(assets),
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        risks = []
        if re.search(r'-----BEGIN .* PRIVATE KEY-----', content): risks.append("Private Key")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks
        todos = len(re.findall(r'(TODO|FIXME)', content, re.IGNORECASE))
        if todos > 0: metrics['todo_count'] = todos
        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
