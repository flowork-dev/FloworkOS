########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\py.py total lines 109 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
import ast
from .base import BaseParser

class PythonParser(BaseParser):
    """
    SPECIALIST PARSER FOR PYTHON FILES (.py)
    Capabilities:
    1. AST Analysis for Imports, Classes, and Functions.
    2. Genealogy Mapping (Class Inheritance).
    3. Call Tracking (Detecting who I am calling).
    4. Security Scanning (Secret Hunter).
    """

    def __init__(self):
        super().__init__() # Ensure base attributes are loaded
        self.color = "#3572A5"  # Python Blue
        self.icon = "f3e2"      # Python Icon
        self.priority = 100     # High priority for specific matcher

    def supports(self, filename, ext):
        return ext == "py"

    def parse(self, content, path):
        """
        Main parsing logic using Abstract Syntax Tree (AST).
        """
        imports = set()
        calls = set() # [ADDED] Track explicit calls to functions/classes
        structure = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.add(n.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            calls.add(f"{node.func.value.id}.{node.func.attr}")

                elif isinstance(node, ast.ClassDef):
                    bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    structure.append({
                        "name": node.name,
                        "type": "class",
                        "line": node.lineno,
                        "parents": bases,
                        "icon": "fa-cube"
                    })
                elif isinstance(node, ast.FunctionDef):
                    structure.append({
                        "name": node.name,
                        "type": "function",
                        "line": node.lineno,
                        "icon": "fa-code"
                    })
        except:
            pass

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "calls": list(calls), # [ADDED] Return calls data
            "assets": [],
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        """
        THE SECRET HUNTER
        Scans for potential hardcoded secrets using regex patterns.
        """
        risks = []
        patterns = {
            "OpenAI Key": r"sk-[a-zA-Z0-9]{32,}",
            "GitHub Token": r"ghp_[a-zA-Z0-9]{30,}",
            "AWS Access Key": r"AKIA[0-9A-Z]{16}",
            "Generic Secret": r"(?i)(api_key|secret_key|password|token)\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"
        }

        for name, pattern in patterns.items():
            if re.search(pattern, content):
                risks.append(f"Potential {name} detected")

        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks
        if len(security_risks) > 0:
            metrics['health_score'] = "VULNERABLE"
        return metrics
