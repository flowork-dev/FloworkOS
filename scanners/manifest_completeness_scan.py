########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\manifest_completeness_scan.py total lines 86 
########################################################################

import os
import json
from collections import OrderedDict
from .base_scanner import BaseScanner

class ManifestCompletenessScanCore(BaseScanner):

    REQUIRED_FIELDS = {
        "icon_file": "icon.png",
        "author": "Flowork Contributor",
        "email": "Contributor@teetah.art",
        "website": "www.teetah.art"
    }

    IDEAL_KEY_ORDER = [
        "id", "name", "version", "icon_file", "author", "email", "website",
        "description", "type", "entry_point", "tier", "ui_schema", "requires_services"
    ]

    def run_scan(self) -> str:
        self.report("\n[SCAN] === Starting Manifest Completeness & Order Scan ===", "SCAN")

        module_manager = self.kernel.get_service("module_manager_service")
        if not module_manager:
            self._register_finding("  [ERROR] -> ModuleManagerService missing!", severity="CRITICAL")
            return "Scan Failed: Core service missing."

        widget_manager = self.kernel.get_service("widget_manager_service")
        all_components = module_manager.loaded_modules.copy()
        if widget_manager:
            all_components.update(widget_manager.loaded_widgets)

        patched_files_count = 0

        for component_id, data in all_components.items():
            manifest_path = os.path.join(data['path'], 'manifest.json')
            if not os.path.exists(manifest_path):
                continue

            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    original_manifest_data = json.load(f)

                keys_to_add = []
                current_manifest = original_manifest_data.copy()

                for key, default_val in self.REQUIRED_FIELDS.items():
                    if key not in current_manifest:
                        current_manifest[key] = default_val
                        keys_to_add.append(key)

                reordered_manifest = OrderedDict()
                for key in self.IDEAL_KEY_ORDER:
                    if key in current_manifest:
                        reordered_manifest[key] = current_manifest.pop(key)
                for key, value in current_manifest.items():
                    reordered_manifest[key] = value

                needs_update = bool(keys_to_add) or list(original_manifest_data.keys()) != list(reordered_manifest.keys())

                if needs_update:
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        json.dump(reordered_manifest, f, indent=4, ensure_ascii=False)

                    action_log = "reordered keys."
                    if keys_to_add:
                        action_log = f"added missing keys ({', '.join(keys_to_add)}) and reordered."

                    self.report(f"  [PATCH] -> '{component_id}': {action_log}", "WARN")
                    patched_files_count += 1

            except Exception as e:
                self._register_finding(f"  [ERROR] -> Failed processing manifest for '{component_id}': {e}", severity="MAJOR")

        if patched_files_count == 0:
            self.report("  [OK] -> All manifests are compliant.", "OK")

        summary = f"Manifest Scan: {patched_files_count} manifests updated."
        self.report(f"[DONE] {summary}", "SUCCESS")
        return summary
