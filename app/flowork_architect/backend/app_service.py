########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\app_service.py total lines 507 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import time
import threading
import traceback
import csv
import io
import sys
import shutil
import importlib.util
import fnmatch
import logging

from flowork_kernel.services.base_app_service import BaseAppService

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_parser_loader():
    """
    Load parsers with a UNIQUE namespace to avoid collision with other apps.
    Standard 'import parsers' causes conflicts if multiple apps have a 'parsers' folder.
    """
    try:
        init_path = os.path.join(current_dir, "parsers", "__init__.py")
        if os.path.exists(init_path):
            module_name = "flowork_architect.backend.parsers"

            spec = importlib.util.spec_from_file_location(module_name, init_path)
            mod = importlib.util.module_from_spec(spec)

            sys.modules[module_name] = mod

            spec.loader.exec_module(mod)
            return mod.load_parsers_map

        return lambda: []
    except Exception as e:
        print(f"[Cortex] CRITICAL: Cannot load parsers engine: {e}")
        return lambda: []

class ArchitectService(BaseAppService):
    """
    THE CORTEX MANAGER (BRIDGE EDITION)
    Orchestrates scanning, caching, CRUD, and Knowledge Export.
    """

    _SHARED_DATA = None
    _IS_SYNCING = False

    def __init__(self, kernel, service_id):
        self.name = "Flowork Cortex"
        try: super().__init__(kernel, service_id)
        except: self.kernel = kernel; self.service_id = service_id

        self.logger = logging.getLogger("ArchitectService")

        if ArchitectService._SHARED_DATA is None:
            ArchitectService._SHARED_DATA = {
                "graph": {"nodes": [], "edges": [], "zombie_count": 0},
                "details": {},
                "lookup": {}
            }

        self.muscle = None
        if hasattr(self.kernel, 'get_service'):
            self.muscle = self.kernel.get_service("app_runtime")

        if self.muscle:
            self.logger.info("🧠 [Cortex Bridge] Connected to Muscle.")

        if os.path.exists("/master_workspace"):
            self.root_dir = "/master_workspace"
        else:
            self.root_dir = os.getcwd()
            if "flowork_architect" in self.root_dir:
                self.root_dir = os.path.abspath(os.path.join(self.root_dir, "../../../"))

        self.logger.info(f"[{self.name}] Universe Root FIXED to: {self.root_dir}")

        loader = get_parser_loader()
        self.parsers = loader()

        self.app_backend = current_dir
        self.cache_path = os.path.join(self.app_backend, "neural_atlas_cache.json")
        try: os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        except: pass

    async def start(self):
        """Service Lifecycle Start"""
        self.logger.info(f"[{self.name}] Service Started.")
        if os.path.exists(self.cache_path):
             self.run_scan()
        else:
             self.force_sync() # Kalau belum ada, trigger scan

    def force_sync(self):
        """Trigger Full Rescan (bisa via Muscle atau Thread Lokal)"""
        if self.muscle:
            self.logger.info("🚀 [Bridge] Delegating Deep Scan to Muscle...")
            threading.Thread(target=self._run_scan_worker, daemon=True).start()
            return {"status": "success", "message": "Neural Scan Initiated (via Muscle)."}

        if ArchitectService._IS_SYNCING:
            return {"status": "busy", "message": "Cortex is thinking..."}

        thread = threading.Thread(target=self.build_atlas)
        thread.start()
        return {"status": "success", "message": "Neural Scan Initiated (Legacy)."}

    def _run_scan_worker(self):
        """Worker thread untuk memanggil Muscle"""
        try:
            self.muscle.execute_app(
                app_id="flowork_architect",
                action="scan",
                params={"root_dir": self.root_dir},
                user_id="system"
            )
        except Exception as e:
            self.logger.error(f"❌ [Bridge] Scan Failed: {e}")

    def run_scan(self):
        """
        Mengembalikan struktur Graph untuk visualisasi 'Galaxy Ball'.
        CRASH PROOF: Menangani cache kosong/korup.
        """
        try:
            default_graph = {"nodes": [], "edges": [], "zombie_count": 0}

            if not ArchitectService._SHARED_DATA or "graph" not in ArchitectService._SHARED_DATA:
                 ArchitectService._SHARED_DATA = {"graph": default_graph, "details": {}, "lookup": {}}

            current_nodes = ArchitectService._SHARED_DATA["graph"].get("nodes", [])
            if not current_nodes and os.path.exists(self.cache_path):
                try:
                    with open(self.cache_path, "r", encoding='utf-8') as f:
                        data = json.load(f)
                        if "graph" in data:
                            ArchitectService._SHARED_DATA = data
                except Exception as e:
                    self.logger.warning(f"Cache load warning: {e}")

            if not ArchitectService._SHARED_DATA["graph"].get("nodes"):
                threading.Thread(target=self.build_atlas).start()
                return default_graph

            return ArchitectService._SHARED_DATA["graph"]

        except Exception as e:
            self.logger.error(f"run_scan CRITICAL ERROR: {e}")
            traceback.print_exc()
            return {"nodes": [], "edges": [], "zombie_count": 0}

    def get_file_intel(self, path, all_nodes_dummy=None):
        """
        Mengembalikan detail file + Object Node inbound/outbound.
        """
        try:
            if os.path.exists(self.cache_path):
                 try:
                    with open(self.cache_path, "r", encoding='utf-8') as f:
                        data = json.load(f)
                        if "details" in data:
                            ArchitectService._SHARED_DATA = data
                 except: pass

            if not path: return {"status": "error", "message": "No path provided"}

            details_map = ArchitectService._SHARED_DATA.get("details", {})
            nodes_list = ArchitectService._SHARED_DATA.get("graph", {}).get("nodes", [])

            details = details_map.get(path)

            if details:
                inbound_nodes = []
                for p in details.get("inbound_paths", []):
                    if p in details_map:
                        nid = details_map[p]["id"]
                        node = next((n for n in nodes_list if n["id"] == nid), None)
                        if node: inbound_nodes.append(node)

                outbound_nodes = []
                for p in details.get("outbound_paths", []):
                    if p in details_map:
                        nid = details_map[p]["id"]
                        node = next((n for n in nodes_list if n["id"] == nid), None)
                        if node: outbound_nodes.append(node)

                return {
                    "status": "success",
                    "path": path,
                    "content": details.get("content", ""),
                    "structure": details.get("structure", []),
                    "organs": details.get("organs", []),
                    "metrics": details.get("metrics", {}),
                    "dependencies": details.get("raw_assets", []),
                    "calls": details.get("raw_calls", []),
                    "inbound": inbound_nodes,
                    "outbound": outbound_nodes
                }

            return {"status": "error", "message": "File not found in index."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def save_file(self, path, content):
        """Menyimpan file ke disk."""
        if self.muscle:
             self.muscle.execute_app(
                app_id="flowork_architect",
                action="crud",
                params={"crud_action": "create_file", "target_dir": os.path.dirname(path), "name": os.path.basename(path)},
                user_id="system"
            )

        if not path: return {"status": "error"}

        try:
            full_path = os.path.join(self.root_dir, path)
            with open(full_path, "w", encoding="utf-8") as f: f.write(content)

            if ArchitectService._SHARED_DATA and path in ArchitectService._SHARED_DATA.get("details", {}):
                ArchitectService._SHARED_DATA["details"][path]["content"] = content

            return {"status": "success"}
        except Exception as e: return {"status": "error", "message": str(e)}

    def handle_crud(self, payload):
        """Menangani operasi File System (Create/Delete/Rename)"""
        action = payload.get('crud_action') or payload.get('action')

        if self.muscle:
            self.logger.info(f"🛠️ [Bridge] Delegating CRUD '{action}' to Muscle.")
            self.muscle.execute_app(
                app_id="flowork_architect",
                action="crud",
                params={"crud_action": action, **payload},
                user_id="system"
            )
            return {"status": "success", "message": "Operation queued via Muscle."}

        path = payload.get('path')
        try:
            if action == 'create_file':
                target_dir = payload.get('target_dir', '')
                name = payload.get('name')
                full_dir = os.path.join(self.root_dir, target_dir) if target_dir else self.root_dir
                full_path = os.path.join(full_dir, name)
                if os.path.exists(full_path): return {"status": "error", "message": "File exists"}
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f: f.write("")
                threading.Thread(target=self.build_atlas).start()
                return {"status": "success", "path": os.path.relpath(full_path, self.root_dir).replace("\\", "/")}

            elif action == 'create_folder':
                target_dir = payload.get('target_dir', '')
                name = payload.get('name')
                full_dir = os.path.join(self.root_dir, target_dir) if target_dir else self.root_dir
                full_path = os.path.join(full_dir, name)
                if os.path.exists(full_path): return {"status": "error", "message": "Folder exists"}
                os.makedirs(full_path)
                threading.Thread(target=self.build_atlas).start()
                return {"status": "success"}

            elif action == 'rename':
                new_name = payload.get('new_name')
                old_path = os.path.join(self.root_dir, path)
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                threading.Thread(target=self.build_atlas).start()
                return {"status": "success"}

            elif action == 'delete':
                full_path = os.path.join(self.root_dir, path)
                if os.path.isdir(full_path): shutil.rmtree(full_path)
                else: os.remove(full_path)
                if ArchitectService._SHARED_DATA and path in ArchitectService._SHARED_DATA.get("details", {}):
                    del ArchitectService._SHARED_DATA["details"][path]
                threading.Thread(target=self.build_atlas).start()
                return {"status": "success"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def build_atlas(self):
        ArchitectService._IS_SYNCING = True
        self.logger.info(f"[{self.name}] Starting Deep Scan at {self.root_dir}...")

        nodes = []
        file_details = {}
        id_counter = 1
        file_map = {}
        filename_map = {}
        lookup = {}

        try:
            IGNORE_PATTERNS = [
                '.git', '.idea', '.vscode', '.github',
                '.venv', 'venv', 'env',
                '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '*.egg-info',
                'node_modules', 'dist', 'build', 'vendor',
                'cache', 'llama_tools', 'unsloth_compiled_cache',
                'temp_research_audio', 'llama.cpp',
                'backup', 'data', 'logs', '_logs', 'ai_models',
                'nodejs',
                '*.pyc', '*.pyo', '*.pyd', '*.log', '*.db', '*.sqlite3', 'dump.rdb',
                '.env*', '*.env', '.dockerignore', '.gitignore', 'pre_launcher.pid'
            ]

            def is_excluded(name):
                for pattern in IGNORE_PATTERNS:
                    if fnmatch.fnmatch(name, pattern): return True
                return False

            for root, dirs, files in os.walk(self.root_dir):
                dirs[:] = [d for d in dirs if not is_excluded(d)]

                for file in files:
                    if is_excluded(file): continue

                    try:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")
                        parts = file.split('.')
                        ext = parts[-1].lower() if len(parts) > 1 else file.lower()

                        active_parser = None
                        for parser in self.parsers:
                            if parser.supports(file, ext):
                                active_parser = parser
                                break

                        node_color = "#999999"
                        node_icon = "f15b"
                        analysis = {
                            "imports": [], "calls": [], "assets": [], "structure": [], "organs": [],
                            "metrics": {"loc": 0, "complexity": "LOW", "todo_count": 0}
                        }
                        content = ""

                        if active_parser:
                            node_color = active_parser.color
                            node_icon = active_parser.icon
                            try:
                                if ext in ['db', 'sqlite', 'db-shm', 'db-wal', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'pdf', 'exe', 'bin']:
                                    analysis = active_parser.parse(full_path, rel_path)
                                else:
                                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
                                    analysis = active_parser.parse(content, rel_path)
                            except Exception as pe:
                                analysis["structure"] = [{"name": "Parse Error", "type": "error", "icon": "fa-bug"}]
                        else:
                            if ext in ['txt','md','json','yml', 'css', 'js', 'html']:
                                try:
                                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                        content = f.read()
                                        analysis["metrics"]["loc"] = len(content.splitlines())
                                except: pass

                        try: analysis["metrics"]["last_modified"] = os.path.getmtime(full_path)
                        except: analysis["metrics"]["last_modified"] = 0

                        node = {
                            "id": id_counter,
                            "label": file,
                            "title": rel_path,
                            "path": rel_path,
                            "color": node_color,
                            "icon_code": node_icon,
                            "icon_face": "Brands" if ext in ["py", "js", "html", "css", "vue"] else "Free",
                            "group": rel_path.split('/')[0],
                            "ext": ext,
                            "is_zombie": False
                        }
                        nodes.append(node)

                        file_map[rel_path] = node["id"]
                        lookup[node["id"]] = rel_path
                        if file not in filename_map: filename_map[file] = []
                        filename_map[file].append(rel_path)

                        stored_content = content if isinstance(content, str) and len(content) < 100000 else "[LARGE/BINARY FILE]"

                        file_details[rel_path] = {
                            "id": node["id"],
                            "content": stored_content,
                            "structure": analysis.get("structure", []),
                            "organs": analysis.get("organs", []),
                            "metrics": analysis.get("metrics", {}),
                            "raw_imports": list(analysis.get("imports", [])),
                            "raw_calls": list(analysis.get("calls", [])),
                            "raw_assets": list(analysis.get("assets", [])),
                            "inbound_paths": [],
                            "outbound_paths": []
                        }
                        id_counter += 1

                    except Exception as file_e: continue

            self.logger.info(f"[{self.name}] Wiring Nodes ({len(nodes)} files)...")
            edges = []
            unique_edges = set()

            def add_edge(src_path, tgt_path):
                if src_path == tgt_path: return
                if tgt_path not in file_details: return
                s_id = file_details[src_path]["id"]
                t_id = file_details[tgt_path]["id"]
                key = f"{s_id}-{t_id}"
                if key not in unique_edges:
                    if tgt_path not in file_details[src_path]["outbound_paths"]:
                        file_details[src_path]["outbound_paths"].append(tgt_path)
                    if src_path not in file_details[tgt_path]["inbound_paths"]:
                        file_details[tgt_path]["inbound_paths"].append(src_path)
                    edges.append({"from": s_id, "to": t_id, "arrows": "to", "color": {"color": "#666", "opacity": 0.3}})
                    unique_edges.add(key)

            for path, details in file_details.items():
                synapses = set(details["raw_imports"]) | set(details["raw_calls"])

                for imp in synapses:
                    if imp in file_details:
                        add_edge(path, imp)
                        continue

                    target_name = imp.split('.')[-1] if '.' in imp else imp
                    candidates = []
                    possible_names = [target_name, f"{target_name}.py", f"{target_name}.js", f"{target_name}.vue", f"{target_name}.html", f"{target_name}.css"]
                    for pname in possible_names:
                        if pname in filename_map: candidates.extend(filename_map[pname])

                    if candidates:
                        add_edge(path, candidates[0])

            zombie_count = 0
            safe_names = ['index.html', 'main.py', 'app.py', 'server.py', 'router.py', 'manage.py', 'start_flowork.py', 'requirements.txt', 'package.json', 'Dockerfile', 'docker-compose.yml', 'app_service.py', 'app_router.py']
            for path, details in file_details.items():
                if len(details['inbound_paths']) == 0:
                    is_safe = False
                    fname = path.split('/')[-1].lower()
                    if fname in safe_names: is_safe = True
                    if path.startswith('app/') or path.startswith('flowork-core/'): is_safe = True
                    if "router" in fname or "service" in fname: is_safe = True
                    if fname.endswith(('.md', '.txt', '.csv', '.sql', '.env')): is_safe = True

                    if not is_safe:
                        for n in nodes:
                            if n['id'] == details['id']:
                                n['is_zombie'] = True
                                n['color'] = '#ff4444'
                                zombie_count += 1

            ArchitectService._SHARED_DATA = {
                "graph": {"nodes": nodes, "edges": edges, "zombie_count": zombie_count},
                "details": file_details,
                "lookup": lookup,
                "ts": time.time()
            }

            with open(self.cache_path, "w") as f:
                json.dump(ArchitectService._SHARED_DATA, f)

            self.logger.info(f"[{self.name}] Scan Success at {self.root_dir}. Saved {len(nodes)} nodes.")

        except Exception as e:
            self.logger.error(f"[{self.name}] GLOBAL SCAN ERROR: {e}")
            traceback.print_exc()
        finally:
            ArchitectService._IS_SYNCING = False

    def export_atlas(self):
        """Export Graph ke CSV"""
        try:
            si = io.StringIO()
            si.write('\ufeff')
            cw = csv.writer(si, quoting=csv.QUOTE_ALL)
            cw.writerow(["FILE_PATH", "TYPE", "INBOUND", "OUTBOUND", "DEPENDENCIES", "STRUCTURE"])

            nodes = ArchitectService._SHARED_DATA.get("graph", {}).get("nodes", [])
            details = ArchitectService._SHARED_DATA.get("details", {})

            for node in nodes:
                path = node["path"]
                detail = details.get(path, {})
                cw.writerow([path, node.get("ext", "").upper(), detail.get("inbound_paths"), detail.get("outbound_paths"), detail.get("raw_assets"), detail.get("structure")])
            return {"status": "success", "csv": si.getvalue()}
        except Exception as e: return {"status": "error", "message": str(e)}

    def export_json_atlas(self):
        """Export Graph ke JSON"""
        try:
            nodes = ArchitectService._SHARED_DATA.get("graph", {}).get("nodes", [])
            details = ArchitectService._SHARED_DATA.get("details", {})
            data_export = []
            for node in nodes:
                path = node["path"]
                detail = details.get(path, {})
                item = {"file_path": path, "type": node.get("ext", "").upper(), "inbound": detail.get("inbound_paths"), "outbound": detail.get("outbound_paths"), "structure": detail.get("structure")}
                data_export.append(item)
            return {"status": "success", "json": json.dumps(data_export, indent=2)}
        except Exception as e: return {"status": "error", "message": str(e)}
