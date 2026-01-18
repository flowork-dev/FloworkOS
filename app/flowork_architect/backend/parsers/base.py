########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\base.py total lines 51 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re

class BaseParser:
    """
    Base class for all file parsers.
    Standardizes the interface for the Cortex scanner.
    """
    def __init__(self):
        self.color = "#999999"
        self.icon = "f15b"
        self.priority = 0 # Default priority (Lowest)

    def supports(self, filename, ext):
        return False

    def parse(self, content, path):
        """
        Default behavior: basic regex scan
        """
        return {
            "imports": [],
            "assets": [],
            "structure": [],
            "metrics": self.analyze_vital_signs(content)
        }

    def analyze_vital_signs(self, content):
        """
        Generic analyzer. Override this in subclasses for specific logic.
        """
        try:
            loc = len(content.splitlines())
            todos = len(re.findall(r'(TODO|FIXME|HACK|BUG|DANGER)', content, re.IGNORECASE))

            complexity = "LOW"
            if loc > 300: complexity = "HIGH"
            elif loc > 100: complexity = "MEDIUM"

            return {
                "loc": loc,
                "complexity": complexity,
                "todo_count": todos
            }
        except Exception:
            return {"loc": 0, "complexity": "LOW", "todo_count": 0}
