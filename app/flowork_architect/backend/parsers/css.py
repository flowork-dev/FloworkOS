########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\css.py total lines 93 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class CssParser(BaseParser):
    """
    SPECIALIST PARSER FOR STYLESHEETS (.css, .scss, .sass, .less)
    Capabilities:
    1. Structure: Identifies CSS Selectors (.class, #id).
    2. Assets: Finds url() references to images/fonts.
    3. Wiring: Finds @import references.
    """

    def __init__(self):
        super().__init__()
        self.color = "#2965f1"  # CSS3 Blue
        self.icon = "f38b"      # CSS3 Shield Icon
        self.priority = 80      # Standard Priority

    def supports(self, filename, ext):
        return ext in ["css", "scss", "sass", "less"]

    def parse(self, content, path):
        imports = set()
        assets = set()
        structure = []

        url_pattern = r'url\([\'"]?([^\'"\)]+)[\'"]?\)'
        import_pattern = r'@import\s+[\'"]([^\'"]+)[\'"]'

        for match in re.findall(url_pattern, content):
            if not match.startswith("data:") and not match.startswith("http"):
                clean = match.split('?')[0].split('/')[-1]
                assets.add(clean)
                if clean.endswith('.css') or clean.endswith('.scss'):
                    imports.add(clean)

        for match in re.findall(import_pattern, content):
            clean = match.split('/')[-1]
            imports.add(clean)

        files_pattern = r'[\w\-\.\/]+\.(?:png|jpg|svg|woff|woff2|ttf|eot)'
        for match in re.findall(files_pattern, content):
            clean_name = match.split('/')[-1]
            assets.add(clean_name)

        selector_pattern = r'^([^{]+)\{'

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line: continue

            if line.startswith('@'): continue

            match = re.search(selector_pattern, line)
            if match:
                selectors = match.group(1).strip().split(',')
                primary_sel = selectors[0].strip()

                icon = "fa-asterisk" # Default element
                s_type = "element"

                if primary_sel.startswith('.'):
                    icon = "fa-bullseye"
                    s_type = "class"
                elif primary_sel.startswith('#'):
                    icon = "fa-hashtag"
                    s_type = "id"

                structure.append({
                    "name": primary_sel,
                    "type": s_type,
                    "line": line_num,
                    "icon": icon
                })

        return {
            "imports": list(imports),
            "assets": list(assets),
            "structure": structure,
            "metrics": self.analyze_vital_signs(content)
        }

    def analyze_vital_signs(self, content):
        metrics = super().analyze_vital_signs(content)
        todos = len(re.findall(r'/\*.*?(TODO|FIXME).*?\*/', content, re.IGNORECASE))
        if todos > 0: metrics['todo_count'] = todos
        return metrics
