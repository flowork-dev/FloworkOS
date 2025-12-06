########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\core_compiler_health_scan.py total lines 65 
########################################################################

import os
from .base_scanner import BaseScanner

class CoreCompilerHealthScan(BaseScanner):

    def run_scan(self) -> str:
        self.report("\n[SCAN] === Starting Core Compiler Health Scan ===", "SCAN")

        compiler_path = os.path.join(self.kernel.project_root_path, "modules", "core_compiler_module", "processor.py")
        generated_services_path = os.path.join(self.kernel.project_root_path, "generated_services")

        checks_passed = 0
        total_checks = 2 # Cek source code + Cek output folder

        target_code = 'os.path.join(self.kernel.project_root_path, "core_services")'

        found, _ = self._check_file_content(compiler_path, target_code)
        if not found:
             found, _ = self._check_file_content(compiler_path, target_code.replace('"', "'"))

        if found:
            checks_passed += 1
            self.report("  [OK] -> Compiler source logic verified.", "OK")
        else:
            self._register_finding(
                "  [CRITICAL] -> Compiler logic mismatch! Ensure it points to 'core_services'.",
                context={"file": compiler_path},
                severity="CRITICAL"
            )

        if os.path.exists(generated_services_path):
            services = [d for d in os.listdir(generated_services_path) if os.path.isdir(os.path.join(generated_services_path, d)) and not d.startswith("__")]
            if services:
                checks_passed += 1
                self.report(f"  [OK] -> Generated services found: {len(services)} active.", "OK")
            else:
                self.report("  [WARN] -> 'generated_services' folder exists but is empty. Run Compiler immediately.", "WARN")
        else:
            self.report("  [WARN] -> 'generated_services' folder missing. Compiler has strictly never run.", "WARN")

        summary = f"Core Compiler Health: {checks_passed}/{total_checks} checks passed."
        status = "SUCCESS" if checks_passed == total_checks else "WARN"
        self.report(f"[DONE] {summary}", status)
        return summary

    def _check_file_content(self, file_path, content_to_find):
        if not os.path.exists(file_path):
            self._register_finding(f"  [ERROR] File not found: {file_path}", severity="MAJOR")
            return False, None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content_to_find in content:
                    return True, None
                return False, content[:100] # Return snippet for debug
        except Exception as e:
            self._register_finding(f"  [ERROR] Error reading {file_path}: {e}", severity="MAJOR")
            return False, None
