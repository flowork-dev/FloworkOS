########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\core_integrity_scan.py total lines 63 
########################################################################

import os
import json
from .base_scanner import BaseScanner

class CacheIntegrityScan(BaseScanner):

    def run_scan(self) -> str:
        self.report("\n[SCAN] === Starting Component Cache Integrity Scan ===", "SCAN")

        services_to_check = [
            ("ModuleManager", "flowork_kernel/services/module_manager_service/module_manager_service.py", "module_index.cache"),
            ("WidgetManager", "flowork_kernel/services/widget_manager_service/widget_manager_service.py", "widget_index.cache"),
            ("TriggerManager", "flowork_kernel/services/trigger_manager_service/trigger_manager_service.py", "trigger_index.cache")
        ]

        checks_passed = 0
        total_checks = len(services_to_check) * 2 # Cek file service + Cek file cache

        for service_name, service_path_rel, cache_filename in services_to_check:
            service_path_abs = os.path.join(self.kernel.project_root_path, service_path_rel)
            cache_path_abs = os.path.join(self.kernel.data_path, cache_filename)

            if os.path.exists(service_path_abs):
                checks_passed += 1 # Service exist is good
            else:
                self._register_finding(
                    f"  [CRITICAL] -> Service source for {service_name} missing!",
                    context={"file": service_path_abs},
                    severity="CRITICAL"
                )

            if os.path.exists(cache_path_abs):
                try:
                    with open(cache_path_abs, 'r', encoding='utf-8') as f:
                        json.load(f)
                    self.report(f"  [OK] -> Cache '{cache_filename}' is valid.", "OK")
                    checks_passed += 1
                except json.JSONDecodeError:
                    self._register_finding(
                        f"  [MAJOR] -> Cache '{cache_filename}' corrupted. Auto-rebuild required.",
                        context={"file": cache_path_abs},
                        severity="MAJOR"
                    )
                except Exception as e:
                    self._register_finding(
                        f"  [MAJOR] -> Read error on '{cache_filename}': {e}",
                        context={"file": cache_path_abs},
                        severity="MAJOR"
                    )
            else:
                self.report(f"  [INFO] -> Cache '{cache_filename}' not present (Cold Start).", "INFO")
                checks_passed += 1

        summary = f"Cache Integrity: {checks_passed}/{total_checks} checks passed."
        status = "SUCCESS" if checks_passed == total_checks else "WARN"
        self.report(f"[DONE] {summary}", status)
        return summary
