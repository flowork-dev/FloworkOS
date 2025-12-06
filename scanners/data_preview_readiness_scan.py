########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\data_preview_readiness_scan.py total lines 100 
########################################################################

import os
import re
from .base_scanner import BaseScanner
from flowork_kernel.api_contract import IDataPreviewer

class DataPreviewReadinessScanCore(BaseScanner):

    def run_scan(self) -> str:
        self.report("\n[INFO] === Starting DYNAMIC Data Preview Readiness Scan (V2) ===", "INFO")

        module_manager = self.kernel.get_service("module_manager_service")
        if not module_manager:
            self._register_finding("  [ERROR] -> ModuleManagerService not found!", severity="CRITICAL")
            return "Scan Failed: Core service missing."

        patched_count = 0
        scanned_count = 0

        for module_id, data in module_manager.loaded_modules.items():
            scanned_count += 1

            if not data.get("instance"):
                continue

            instance = data["instance"]
            manifest = data.get("manifest", {})

            if isinstance(instance, IDataPreviewer):
                continue

            is_candidate = False
            if manifest.get("output_schema"):
                is_candidate = True

            keywords = ["data", "api", "scraper", "generator"]
            if not is_candidate:
                text_to_search = (manifest.get("name", "") + manifest.get("description", "")).lower()
                if any(k in text_to_search for k in keywords):
                    is_candidate = True

            if is_candidate:
                self.report(f"  [PATCH] -> Candidate found: {module_id}. Applying IDataPreviewer patch...", "WARN")
                if self._apply_patch(data.get("path")):
                    patched_count += 1

        summary = f"Data Preview Scan: {scanned_count} modules scanned, {patched_count} patched."
        self.report(f"[DONE] {summary}", "SUCCESS")
        return summary

    def _apply_patch(self, module_path):
        """
        Menyuntikkan implementasi default IDataPreviewer ke file processor.py modul target.
        """
        try:
            processor_path = os.path.join(module_path, "processor.py")
            if not os.path.exists(processor_path):
                return False

            with open(processor_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if "IDataPreviewer" not in content:
                import_stmt = "from flowork_kernel.api_contract import IDataPreviewer"
                if "from flowork_kernel.api_contract import" in content:
                    content = content.replace(
                        "from flowork_kernel.api_contract import",
                        "from flowork_kernel.api_contract import IDataPreviewer, "
                    )
                else:
                    content = import_stmt + "\n" + content

            class_pattern = re.compile(r"(class\s+\w+\s*\()([^)]+)(\):)")
            match = class_pattern.search(content)

            if match:
                parents = match.group(2)
                if "IDataPreviewer" not in parents:
                    new_parents = parents + ", IDataPreviewer"
                    content = content.replace(parents, new_parents, 1)

                    method_code = """
    def get_data_preview(self, config: dict):
        return [{"status": "preview_not_available", "message": "Auto-patched: Preview not implemented yet."}]
"""
                    content += method_code

                    with open(processor_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return True

            return False
        except Exception as e:
            self.report(f"    -> Patch failed for {os.path.basename(module_path)}: {e}", "ERROR")
            return False
