########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\cache_integrity_scan.py total lines 51 
########################################################################

import os
from .base_scanner import BaseScanner

class CoreIntegrityScan(BaseScanner):

    def run_scan(self) -> str:
        self.report("\n[SCAN] === Starting Core Integrity Vitals Scan ===", "SCAN")

        startup_service_path = os.path.join(
            self.kernel.project_root_path,
            "flowork_kernel", "services", "startup_service", "startup_service.py"
        )

        checks_passed = 0
        total_checks = 1

        target_code = 'self.kernel.get_service("integrity_checker_service").verify_core_files()'

        if self._check_content(startup_service_path, target_code):
            checks_passed += 1
            self.report("  [OK] -> Vitals check passed: 'Benteng Baja' integrity check is active.", "OK")
        else:
            self._register_finding(
                "  [CRITICAL] -> Security Regression! The integrity check call is missing from StartupService.",
                context={"file": startup_service_path},
                severity="CRITICAL"
            )

        summary = f"Core Integrity Vitals: {checks_passed}/{total_checks} checks passed."
        status = "SUCCESS" if checks_passed == total_checks else "WARN"
        self.report(f"[DONE] {summary}", status)

        return summary

    def _check_content(self, file_path, text_to_find):
        if not os.path.exists(file_path):
            self.report(f"  [ERROR] File not found: {file_path}", "MAJOR")
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return text_to_find in content or text_to_find.replace('"', "'") in content
        except Exception as e:
            self.report(f"  [ERROR] Read failed: {e}", "MAJOR")
            return False
