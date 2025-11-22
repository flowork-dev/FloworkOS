########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scanner_manager_service\scanner_manager_service.py total lines 98 
########################################################################

import os
import re
import importlib
import inspect
import sys
from ..base_service import BaseService
from scanners.base_scanner import BaseScanner
from importlib.machinery import ExtensionFileLoader
class ScannerManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)

        self.scanners_dir = self.kernel.scanners_path
        self.loaded_scanners = {}
        self.logger(f"Service '{self.service_id}' initialized.", "DEBUG")
    def discover_and_load_scanners(self):

        self.logger(
            "ScannerManager: Discovering all scanner modules...", "INFO"
        )
        self.loaded_scanners.clear()
        if not os.path.isdir(self.scanners_dir):
            self.logger(
                f"Scanner directory not found at '{self.scanners_dir}'. Skipping scan.",
                "WARN",
            )
            return


        scanners_parent_dir = os.path.abspath(os.path.join(self.scanners_dir, ".."))
        if scanners_parent_dir not in sys.path:
             sys.path.insert(0, scanners_parent_dir)
             self.logger(f"ScannerManager: Added {scanners_parent_dir} to sys.path for import.", "DEBUG")

        py_files = {
            f.replace(".py", "")
            for f in os.listdir(self.scanners_dir)
            if f.endswith(".py") and not f.startswith("__")
        }
        for module_name_base in py_files:
            source_file_path = os.path.join(self.scanners_dir, f"{module_name_base}.py")
            native_file_path = os.path.join(
                self.scanners_dir, f"{module_name_base}.scanner.flowork"
            )
            path_to_load = None
            is_native_module = False
            if os.path.exists(native_file_path):
                path_to_load = native_file_path
                is_native_module = True
            elif os.path.exists(source_file_path):
                path_to_load = source_file_path
            if not path_to_load:
                continue
            module_name = f"scanners.{module_name_base}"
            try:
                if is_native_module:
                    loader = ExtensionFileLoader(module_name, path_to_load)
                    spec = importlib.util.spec_from_loader(loader.name, loader)
                else:
                    spec = importlib.util.spec_from_file_location(
                        module_name, path_to_load
                    )
                if spec is None:
                    self.logger(
                        f"Could not create spec for {module_name} from {path_to_load}",
                        "WARN",
                    )
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = (
                    module
                )
                spec.loader.exec_module(module)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseScanner) and obj is not BaseScanner:
                        self.loaded_scanners[obj.__name__] = obj
                        self.logger(
                            f"  -> Discovered scanner: '{name}'", "SUCCESS"
                        )
            except Exception as e:
                self.logger(
                    f"ScannerManager: Failed to import scanner from '{module_name_base}': {e}",
                    "ERROR",
                )
        self.logger(
            f"Scanner discovery complete. Found {len(self.loaded_scanners)} scanners.",
            "INFO",
        )
    def get_all_scanners(self):

        return list(self.loaded_scanners.values())
