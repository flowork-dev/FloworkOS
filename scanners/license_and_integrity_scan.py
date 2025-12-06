########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\license_and_integrity_scan.py total lines 70 
########################################################################

import os
import re
from .base_scanner import BaseScanner

class PhaseOneIntegrityScan(BaseScanner):

    def run_scan(self) -> str:
        self.report("\n[SCAN] === Starting Phase 1: Independence Integrity Scan (Doctor Code) ===", "SCAN")

        target_paths = [
            os.path.join(self.kernel.project_root_path, "flowork_kernel", "ui_shell"),
            os.path.join(self.kernel.project_root_path, "widgets"),
            os.path.join(self.kernel.project_root_path, "plugins"),
            os.path.join(self.kernel.project_root_path, "modules")
        ]

        illegal_pattern = re.compile(r"self\.kernel\.get_service\([\"']([\w_]+)[\"']\)\.([\w_]+)\((.*)\)")

        files_scanned = 0
        total_violations_found = 0
        total_violations_healed = 0

        for base_path in target_paths:
            if not os.path.isdir(base_path):
                continue

            for root, _, files in os.walk(base_path):
                if 'scanners' in root or '__pycache__' in root:
                    continue

                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        files_scanned += 1

                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            matches = list(illegal_pattern.finditer(content))
                            if matches:
                                total_violations_found += len(matches)
                                rel_path = os.path.relpath(file_path, self.kernel.project_root_path)
                                self._register_finding(
                                    f"  [WARN] -> Violation found in '{rel_path}' ({len(matches)} instances). Direct kernel service access detected.",
                                    context={"file": file_path},
                                    severity="MAJOR"
                                )


                        except Exception as e:
                            self.report(f"  [ERROR] -> Read failed for {file}: {e}", "ERROR")

        if total_violations_found == 0:
            self.report(f"  [OK] -> Clean architecture verified. No direct kernel coupling found in {files_scanned} files.", "OK")

        summary = f"Phase 1 Scan: Scanned {files_scanned} files. Found {total_violations_found} architectural violations."
        status = "SUCCESS" if total_violations_found == 0 else "WARN"
        self.report(f"[DONE] {summary}", status)

        return summary

    def _auto_patch_file(self, file_path, current_content, match):
        return None, current_content
