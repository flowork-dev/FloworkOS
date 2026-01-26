########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\main.py total lines 230 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import json
import time
import shutil
import traceback
import io
import csv
import fnmatch
import importlib.util

try:
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
except:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

CACHE_FILE = os.path.join(BACKEND_DIR, "neural_atlas_cache.json")

def get_parser_loader():
    try:
        init_path = os.path.join(BACKEND_DIR, "parsers", "__init__.py")
        if os.path.exists(init_path):
            spec = importlib.util.spec_from_file_location("parsers", init_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["parsers"] = mod
            spec.loader.exec_module(mod)
            return mod.load_parsers_map
    except Exception as e:
        print(f"⚠️ [Cortex] Parser loader warning: {e}", flush=True)
    return lambda: []

class CortexBrain:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.parsers = get_parser_loader()()
        self.data = self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"graph": {"nodes": [], "edges": [], "zombie_count": 0}, "details": {}, "lookup": {}}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"❌ [Cortex] Failed to save cache: {e}", flush=True)

    def scan(self):
        print(f"⚡ [Cortex] Starting Deep Scan at: {self.root_dir}", flush=True)

        nodes = []
        file_details = {}
        id_counter = 1
        file_map = {}
        filename_map = {}
        lookup = {}

        IGNORE_PATTERNS = [
            '.git', '.idea', '.vscode', '__pycache__', 'node_modules', 'dist', 'build',
            'venv', 'env', '*.pyc', '*.log', '*.db', '*.sqlite3', '.env*',
            'llama_tools', 'temp_research_audio', 'data', 'logs'
        ]

        def is_excluded(name):
            return any(fnmatch.fnmatch(name, p) for p in IGNORE_PATTERNS)

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not is_excluded(d)]
            for file in files:
                if is_excluded(file): continue
                try:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")
                    ext = file.split('.')[-1].lower() if '.' in file else file.lower()

                    active_parser = None
                    for parser in self.parsers:
                        if parser.supports(file, ext):
                            active_parser = parser
                            break

                    analysis = {"structure": [], "metrics": {}, "imports": [], "calls": [], "assets": []}
                    content = ""
                    node_icon = "f15b"
                    node_color = "#999999"

                    if active_parser:
                        node_color = active_parser.color
                        node_icon = active_parser.icon
                        try:
                            if ext not in ['png','jpg','exe','bin','zip']:
                                with open(full_path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
                                analysis = active_parser.parse(content, rel_path)
                        except: pass

                    node = {
                        "id": id_counter, "label": file, "title": rel_path, "path": rel_path,
                        "color": node_color, "icon_code": node_icon, "ext": ext, "is_zombie": False,
                        "icon_face": "Brands" if ext in ["py", "js", "html", "css", "vue"] else "Free"
                    }
                    nodes.append(node)
                    file_map[rel_path] = node["id"]
                    lookup[node["id"]] = rel_path
                    if file not in filename_map: filename_map[file] = []
                    filename_map[file].append(rel_path)

                    file_details[rel_path] = {
                        "id": node["id"],
                        "content": content[:100000],
                        "structure": analysis.get("structure", []),
                        "metrics": analysis.get("metrics", {}),
                        "raw_imports": list(analysis.get("imports", [])),
                        "raw_calls": list(analysis.get("calls", [])),
                        "inbound_paths": [], "outbound_paths": []
                    }
                    id_counter += 1
                except Exception as e: pass

        edges = []
        unique_edges = set()
        for path, details in file_details.items():
            synapses = set(details["raw_imports"]) | set(details["raw_calls"])
            for imp in synapses:
                target_path = None
                if imp in file_details: target_path = imp
                else:
                    target_name = imp.split('.')[-1]
                    if target_name in filename_map: target_path = filename_map[target_name][0]
                if target_path:
                    s_id = details["id"]
                    t_id = file_details[target_path]["id"]
                    key = f"{s_id}-{t_id}"
                    if key not in unique_edges and s_id != t_id:
                        edges.append({"from": s_id, "to": t_id, "arrows": "to"})
                        unique_edges.add(key)
                        file_details[path]["outbound_paths"].append(target_path)
                        file_details[target_path]["inbound_paths"].append(path)

        self.data = {
            "graph": {"nodes": nodes, "edges": edges, "zombie_count": 0},
            "details": file_details,
            "lookup": lookup,
            "ts": time.time()
        }
        self._save_cache()

        print(f"✅ [Cortex] Scan Complete. Nodes: {len(nodes)}", flush=True)
        return {"status": "success", "data": self.data["graph"]}

    def get_intel(self, path):
        if not path: return {"status": "error", "message": "Path required"}
        details = self.data["details"].get(path)
        if details:
            nodes_list = self.data["graph"]["nodes"]
            inbound_nodes = []
            for p in details.get("inbound_paths", []):
                if p in self.data["details"]:
                    nid = self.data["details"][p]["id"]
                    node = next((n for n in nodes_list if n["id"] == nid), None)
                    if node: inbound_nodes.append(node)

            outbound_nodes = []
            for p in details.get("outbound_paths", []):
                if p in self.data["details"]:
                    nid = self.data["details"][p]["id"]
                    node = next((n for n in nodes_list if n["id"] == nid), None)
                    if node: outbound_nodes.append(node)

            return {
                "status": "success",
                "content": details.get("content", ""),
                "structure": details.get("structure", []),
                "inbound": inbound_nodes,
                "outbound": outbound_nodes,
                "metrics": details.get("metrics", {}),
                "dependencies": details.get("raw_assets", []),
                "calls": details.get("raw_calls", [])
            }
        return {"status": "error", "message": "File not indexed"}

    def crud(self, action, payload):
        return {"status": "success"}

if __name__ == "__main__":
    payload_str = os.environ.get("FLOWORK_PAYLOAD")
    if not payload_str:
        if len(sys.argv) > 1: payload_str = sys.argv[1]
        else: sys.exit(0)

    try:
        payload = json.loads(payload_str)
        action = payload.get("action")
        params = payload.get("params", {})
        root = params.get("root_dir") or os.getcwd()

        brain = CortexBrain(root)
        result = {}

        if action == "scan" or action == "force_sync":
            result = brain.scan()
        elif action == "get_intel":
            result = brain.get_intel(params.get("path"))
        elif action == "crud":
            result = brain.crud(params.get("crud_action"), params)
        else:
            result = {"status": "error", "error": f"Unknown action: {action}"}

        print(json.dumps(result), flush=True)

    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), flush=True)
        sys.exit(1)
