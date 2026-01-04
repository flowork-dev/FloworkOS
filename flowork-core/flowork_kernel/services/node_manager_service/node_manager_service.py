########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\node_manager_service\node_manager_service.py total lines 210 
########################################################################

import os
import json
import importlib.util
import sys
import logging
import inspect
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.utils.path_helper import get_apps_directory

class NodeManagerService(BaseService):
    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)
        self.nodes_map = {}
        self.nodes_metadata = []
        self.base_apps_path = os.environ.get("FLOWORK_APPS_DIR", str(get_apps_directory()))

    def start(self):
        self.logger.info("🧠 [NodeManager] Syncing Neural Nodes & Logic Modules...")
        self.scan_nodes()
        self.logger.info(f"✅ [NodeManager] Registered {len(self.nodes_map)} Active Nodes.")

    def scan_nodes(self):
        self.nodes_map = {}
        self.nodes_metadata = []

        if not os.path.exists(self.base_apps_path):
            self.logger.warning(f"⚠️ Apps directory not found: {self.base_apps_path}")
            return

        for app_dir in os.listdir(self.base_apps_path):
            full_app_path = os.path.join(self.base_apps_path, app_dir)
            manifest_path = os.path.join(full_app_path, "manifest.json")

            if os.path.isdir(full_app_path):
                if os.path.exists(manifest_path):
                    self._process_manifest(full_app_path, manifest_path, app_dir)
                else:
                    pass

    def _process_manifest(self, app_path, manifest_path, app_folder_name):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            app_id = manifest.get("id", app_folder_name)
            nodes_def = manifest.get("nodes", [])

            if not nodes_def:
                return

            for node_cfg in nodes_def:
                self._load_single_node(app_path, node_cfg, manifest)

        except Exception as e:
            self.logger.error(f"❌ Failed to parse manifest for {app_folder_name}: {e}")

    def _load_single_node(self, app_root, node_cfg, manifest):
        try:
            node_id = node_cfg.get("id")
            rel_path = node_cfg.get("file")
            entry_class = node_cfg.get("entry_class")
            app_id = manifest.get("id")

            if not node_id or not rel_path or not entry_class: return

            source_file = os.path.join(app_root, rel_path)
            if not os.path.exists(source_file):
                if os.path.exists(os.path.join(app_root, "backend", rel_path)):
                    source_file = os.path.join(app_root, "backend", rel_path)
                else:
                    self.logger.warning(f"⚠️ Node file missing for {node_id}: {source_file}")
                    return

            self._register_node_class(node_id, app_id, source_file, entry_class, node_cfg, manifest)

        except Exception as e:
            self.logger.error(f"❌ Error loading node {node_cfg.get('id')}: {e}")

    def _register_node_class(self, node_id, app_id, source_file, entry_class_name, node_cfg=None, manifest=None):
        try:
            node_dir = os.path.dirname(source_file)
            if node_dir not in sys.path:
                sys.path.insert(0, node_dir)

            unique_module_name = f"flowork_nodes.{app_id}.{node_id}".replace("-", "_")

            spec = importlib.util.spec_from_file_location(unique_module_name, source_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[unique_module_name] = mod
                spec.loader.exec_module(mod)

                if hasattr(mod, entry_class_name):
                    node_cls = getattr(mod, entry_class_name)
                    self.nodes_map[node_id] = node_cls

                    if node_cfg and manifest:
                        self.nodes_metadata.append({
                            "id": node_id,
                            "name": node_cfg.get("name", node_id),
                            "category": manifest.get("category", "General"),
                            "app_id": app_id,
                            "inputs": node_cfg.get("inputs", []),
                            "outputs": node_cfg.get("outputs", [])
                        })
                    self.logger.info(f"✅ [Registered] Node: {node_id} | Class: {entry_class_name}")
                    return node_cls
                else:
                    self.logger.error(f"❌ Class '{entry_class_name}' not found in module {unique_module_name}")

            if node_dir in sys.path:
                sys.path.remove(node_dir)
        except Exception as e:
            self.logger.error(f"❌ Registration Failed for {node_id}: {e}")
        return None

    def get_node_class(self, node_id):
        return self.nodes_map.get(node_id)

    def get_node_instance(self, node_id):
        """
        [CRITICAL UPGRADE] Mengambil Instance Node dengan Dependency Injection (Kernel).
        Ini wajib agar Node bisa memanggil 'app_runtime' (Muscle).
        """
        node_cls = self.get_node_class(node_id)

        if not node_cls:
            self.logger.warning(f"🕵️‍♂️ Node '{node_id}' not in registry. Attempting Heuristic Discovery...")
            node_cls = self._attempt_heuristic_discovery(node_id)

        if node_cls:
            try:
                self.logger.info(f"🧬 Instantiating Node '{node_id}' with Kernel injection...")

                try:
                    return node_cls(node_id=node_id, properties={}, kernel=self.kernel)
                except TypeError:
                    self.logger.warning(f"⚠️ Node '{node_id}' rejected arguments (Legacy Node?). Trying empty init.")
                    return node_cls()

            except Exception as e:
                self.logger.error(f"❌ FATAL: Failed to instantiate node '{node_id}'. Error: {e}")
                return None
        else:
            self.logger.error(f"❌ Node ID '{node_id}' ABSOLUTELY NOT FOUND anywhere.")
            return None

    def _attempt_heuristic_discovery(self, node_id):
        """
        [ZERO MAINTENANCE] Mode Detektif:
        Mencari class node secara brute-force di folder app jika manifest.json berantakan.
        """
        target_app_path = os.path.join(self.base_apps_path, node_id)

        if not os.path.exists(target_app_path):
            for d in os.listdir(self.base_apps_path):
                if d.lower() == node_id.lower():
                    target_app_path = os.path.join(self.base_apps_path, d)
                    break

        if not os.path.exists(target_app_path):
            self.logger.error(f"🕵️‍♂️ Directory not found for heuristic search: {target_app_path}")
            return None

        candidates = [
            "node.py",
            "app_node.py",
            "main.py",
            os.path.join("backend", "node.py"),
            os.path.join("backend", "app_node.py"),
            f"{node_id}.py"
        ]

        for cand in candidates:
            file_path = os.path.join(target_app_path, cand)
            if os.path.exists(file_path):
                self.logger.info(f"🕵️‍♂️ Found potential node file: {file_path}")

                try:
                    unique_name = f"flowork_adhoc.{node_id}_{cand.replace('/', '_').replace('.', '_')}"

                    spec = importlib.util.spec_from_file_location(unique_name, file_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[unique_name] = mod
                        spec.loader.exec_module(mod)

                        for name, obj in inspect.getmembers(mod):
                            if inspect.isclass(obj) and obj.__module__ == unique_name:
                                has_run = hasattr(obj, 'run') and callable(getattr(obj, 'run'))
                                has_execute = hasattr(obj, 'execute') and callable(getattr(obj, 'execute'))

                                if has_run or has_execute:
                                    self.logger.info(f"🎯 BINGO! Found compatible Node Class: {name}")
                                    self.nodes_map[node_id] = obj # Cache untuk masa depan
                                    return obj
                except Exception as e:
                    self.logger.warning(f"🕵️‍♂️ Failed inspection on {cand}: {e}")

        self.logger.error(f"🕵️‍♂️ Heuristic search failed. No valid Node class found for '{node_id}'")
        return None

    def get_all_nodes_metadata(self):
        return self.nodes_metadata
