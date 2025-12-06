########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\tier_attribute_scan.py total lines 64 
########################################################################

import os
import re
from .base_scanner import BaseScanner

class TierAttributeScanCore(BaseScanner):

    def run_scan(self) -> str:
        self.report("\n[SCAN] === Starting Tier Attribute Scan ===", "SCAN")

        module_manager = self.kernel.get_service("module_manager_service")
        if not module_manager:
            self._register_finding("  [ERROR] -> ModuleManager missing!", severity="CRITICAL")
            return "Scan Failed."

        missing_tier_count = 0
        checked_count = 0

        tier_pattern = re.compile(r"^\s*TIER\s*=\s*[\"'](free|pro|architect|basic)[\"']", re.MULTILINE | re.IGNORECASE)

        for component_id, data in module_manager.loaded_modules.items():
            checked_count += 1
            manifest = data.get("manifest", {})
            entry_point = manifest.get("entry_point")
            component_path = data.get("path")

            if not entry_point or not component_path:
                continue

            try:
                module_filename = entry_point.split('.')[0]
                processor_path = os.path.join(component_path, f"{module_filename}.py")

                if not os.path.exists(processor_path):
                    processor_path = os.path.join(component_path, "processor.py")
                    if not os.path.exists(processor_path):
                        continue

                with open(processor_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if not tier_pattern.search(content):
                    self._register_finding(
                        f"  [MAJOR] -> Module '{component_id}' is missing valid 'TIER' attribute.",
                        context={"file": processor_path},
                        severity="MAJOR"
                    )
                    missing_tier_count += 1

            except Exception as e:
                self.report(f"  [ERROR] -> Check failed for '{component_id}': {e}", "ERROR")

        if missing_tier_count == 0:
            self.report(f"  [OK] -> All {checked_count} modules have valid TIER attributes.", "OK")

        summary = f"Tier Scan: Found {missing_tier_count} modules missing TIER."
        status = "SUCCESS" if missing_tier_count == 0 else "WARN"
        self.report(f"[DONE] {summary}", status)
        return summary
