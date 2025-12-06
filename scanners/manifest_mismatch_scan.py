########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\manifest_mismatch_scan.py total lines 77 
########################################################################

import os
import json
from .base_scanner import BaseScanner

class ManifestMismatchScan(BaseScanner):

    def run_scan(self) -> str:
        self.report("\n[SCAN] === Starting Manifest vs. Filesystem Mismatch Scan ===", "SCAN")

        root_path = self.kernel.project_root_path
        manifest_path = os.path.join(root_path, "flowork_core", "core_integrity.json")

        if not os.path.exists(manifest_path):
            manifest_path = os.path.join(root_path, "core_integrity.json")
            if not os.path.exists(manifest_path):
                self._register_finding("  [CRITICAL] -> core_integrity.json missing! Integrity check skipped.", severity="CRITICAL")
                return "Scan failed: Manifest missing."

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
                manifest_files = set(manifest_data.keys()) if isinstance(manifest_data, dict) else set(manifest_data)
        except json.JSONDecodeError:
            self._register_finding("  [CRITICAL] -> core_integrity.json corrupted.", severity="CRITICAL")
            return "Scan failed: Manifest corrupted."

        disk_files = set()
        dirs_to_scan = ["flowork_kernel", "services", "scanners", "plugins", "modules"]

        for dir_name in dirs_to_scan:
            full_path = os.path.join(root_path, dir_name)
            if not os.path.exists(full_path):
                continue

            for root, _, files in os.walk(full_path):
                if "__pycache__" in root or ".git" in root:
                    continue

                for file in files:
                    if file.endswith((".pyc", ".log", ".tmp", ".cache")):
                        continue

                    abs_file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_file_path, root_path).replace(os.sep, '/')
                    disk_files.add(rel_path)

        untracked_files = disk_files - manifest_files
        missing_files = manifest_files - disk_files

        if untracked_files:
            count = 0
            for f in sorted(list(untracked_files)):
                if count < 5: # Limit output agar tidak spam
                    self._register_finding(f"  [MAJOR] -> Untracked file: {f}", context={"file": f}, severity="MAJOR")
                count += 1
            if count > 5:
                self.report(f"  ... and {count - 5} more untracked files.", "MAJOR")

        if missing_files:
            for f in sorted(list(missing_files)):
                self._register_finding(f"  [CRITICAL] -> Missing system file: {f}", context={"file": f}, severity="CRITICAL")

        if not untracked_files and not missing_files:
            self.report("  [OK] -> Filesystem matches integrity manifest perfectly.", "OK")
            status = "SUCCESS"
        else:
            status = "WARN"

        summary = f"Integrity Scan: {len(missing_files)} missing, {len(untracked_files)} untracked."
        self.report(f"[DONE] {summary}", status)
        return summary
