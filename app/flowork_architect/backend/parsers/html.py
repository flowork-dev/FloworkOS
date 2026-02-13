########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\html.py total lines 94 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from .base import BaseParser

class HtmlParser(BaseParser):
    """
    SPECIALIST PARSER FOR HTML FILES (.html, .htm)
    Capabilities:
    1. Structure: Semantic Tags (header, main, footer, section).
    2. Asset Detection: script src, link href, img src.
    3. Universal Reference Scanning: Finds filenames in attributes or text.
    4. Security: Scans for comments with sensitive info.
    """

    def __init__(self):
        super().__init__()
        self.color = "#E34F26"  # HTML5 Orange
        self.icon = "f13b"      # HTML5 Icon
        self.priority = 85      # Standard Frontend Priority

    def supports(self, filename, ext):
        return ext in ["html", "htm", "xhtml"]

    def parse(self, content, path):
        imports = set()
        assets = set()
        structure = []

        link_pattern = r'(?:src|href)=["\']([^"\']+)["\']'
        for match in re.findall(link_pattern, content):
            if not match.startswith("http") and not match.startswith("//"):
                clean = match.split('?')[0].split('/')[-1]
                assets.add(clean)
                imports.add(clean) # Dianggap outbound juga

        files_pattern = r'[\w\-\.\/]+\.(?:py|js|json|yml|yaml|vue|css|html|txt|png|jpg)'
        for match in re.findall(files_pattern, content):
            clean_name = match.split('/')[-1]
            current_filename = path.split('/')[-1]
            if clean_name.lower() != current_filename.lower():
                imports.add(clean_name)

        tag_pattern = r'<(\w+)([^>]*)>'
        for line_num, line in enumerate(content.splitlines(), 1):
            match = re.search(tag_pattern, line)
            if match:
                tag = match.group(1)
                attrs = match.group(2)

                if tag in ['header', 'footer', 'main', 'section', 'nav', 'article', 'aside']:
                    structure.append({
                        "name": tag.upper(),
                        "type": "tag",
                        "line": line_num,
                        "icon": "fa-window-maximize"
                    })
                elif tag == 'div' and 'id=' in attrs:
                    id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
                    if id_match:
                        structure.append({
                            "name": f"#{id_match.group(1)}",
                            "type": "id",
                            "line": line_num,
                            "icon": "fa-hashtag"
                        })

        security_risks = self.scan_for_secrets(content)

        return {
            "imports": list(imports),
            "assets": list(assets),
            "structure": structure,
            "metrics": self.analyze_vital_signs(content, security_risks)
        }

    def scan_for_secrets(self, content):
        risks = []
        if re.search(r'(?i)(api_key|token)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{20,}["\']', content):
            risks.append("Potential Exposed Key in HTML")
        return risks

    def analyze_vital_signs(self, content, security_risks):
        metrics = super().analyze_vital_signs(content)
        metrics['security_risks'] = security_risks

        if todos > 0: metrics['todo_count'] = todos

        if len(security_risks) > 0: metrics['complexity'] = "CRITICAL"
        return metrics
