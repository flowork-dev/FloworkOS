########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\dockerfile.py total lines 70 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class DockerfileParser(BaseParser):
    """
    SPECIALIST PARSER FOR DOCKERFILES
    """

    def __init__(self):
        super().__init__()
        self.color = "#2496ED"
        self.icon = "f395"
        self.priority = 90

    def supports(self, filename, ext):
        return filename == "Dockerfile" or ext == "dockerfile"

    def parse(self, content, path):
        imports = set()
        structure = []

        copy_pattern = r'(?:COPY|ADD)\s+["\']?([^"\s]+)'
        for match in re.findall(copy_pattern, content):
            if not match.startswith("--"):
                clean = match.split('/')[-1]
                imports.add(clean)

        exec_pattern = r'[\w\-\.\/]+\.(?:py|sh|bat|js|json|yml)'
        for match in re.findall(exec_pattern, content):
            clean = match.split('/')[-1]
            if clean != "Dockerfile":
                imports.add(clean)

        stage_pattern = r'^(FROM|RUN|CMD|ENTRYPOINT|WORKDIR|ENV|EXPOSE)\s+(.*)'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(stage_pattern, line)
            if match:
                structure.append({
                    "name": match.group(1),
                    "type": "stage",
                    "line": line_num,
                    "icon": "fa-layer-group"
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
        if re.search(r'ENV\s+.*(?:PASSWORD|SECRET|KEY).*=', content):
            risks.append("Hardcoded Env Secret")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks
        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
