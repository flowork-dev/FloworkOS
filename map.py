########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\map.py total lines 261 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import ast
import os
import sys
import fnmatch
from datetime import datetime

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  Pandas tidak ditemukan. Output akan fallback ke CSV.")

class ArchitectureMapperV4:
    def __init__(self, target_path):
        self.target_path = target_path
        self.output_xlsx = "FLOWORK_ARCHITECTURE_MAP_V4.xlsx"
        self.output_csv = "FLOWORK_ARCHITECTURE_MAP_V4.csv"
        self.output_md = "FLOWORK_ARCHITECTURE_MAP_V4.md"

        self.exclude_patterns = [
            '**/.venv*', '**/venv*', '.venv', 'venv',
            '**/cache*', '**/unsloth_compiled_cache*',
            '**/__pycache__', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
            '.git', '.idea', '.vscode', '**/.vscode*',
            'node_modules', 'nodejs', 'vendor', '*.egg-info',
            'flowork-core/llama.cpp',
            'logs', '_logs', 'data', 'backup', 'dump.rdb', 'ai_models',
            'flowork-core/temp_research_audio',
            'assets', 'capsules', 'flowork-cloud', 'flowork-gui',
            'formatters', 'scanners', 'triggers', 'tools',
            '**/migrations', '**/app/capsules', '**/modules', '**/plugins',
            '**/widgets', '**/locales',
            'backup.py', 'clean.py', 'get-pip.py', 'core_legacy_hunter.py',
            'pre_launcher.pid', 'neural_atlas_cache.json', 'BACKUP_FOR_GEMINI.txt',
            '*.pyc', '*.pyo', '*.log', '*.db', '*.sqlite3', '*.md', '*.BAK',
            '*.env*', '*.bat', '*.sh', '.dockerignore', '.gitignore',
            '0-FORCE_REBUILD.bat', '1-STOP_DOCKER*',
            '5-upload_momod_gui.bat', '6-upload_flowork_gui.bat',
            '7-upload-docs.bat', '8.publish.bat', '9.upload_all_project.bat',
            '10.BACKUPENGINE.bat', '11.BACKUPGUI.bat'
        ]

    def is_excluded(self, file_path):
        rel_path = os.path.relpath(file_path, self.target_path).replace('\\', '/')
        filename = os.path.basename(file_path)
        for pattern in self.exclude_patterns:
            clean_pattern = pattern.rstrip('/')
            if filename == clean_pattern: return True
            if fnmatch.fnmatch(rel_path, clean_pattern) or fnmatch.fnmatch(filename, clean_pattern): return True
            if fnmatch.fnmatch(rel_path, f"*/{clean_pattern}"): return True
            if rel_path.startswith(clean_pattern + '/') or rel_path == clean_pattern: return True
        return False

    def _get_loc(self, node):
        """Menghitung Lines of Code (LOC)"""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0

    def _get_complexity(self, node):
        """Menghitung Cyclomatic Complexity sederhana (Jumlah percabangan)"""
        complexity = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler)):
                complexity += 1
            if sys.version_info >= (3, 10) and isinstance(child, ast.Match):
                complexity += len(child.cases)
        return complexity

    def _get_decorators(self, node):
        """Mengambil list decorators"""
        decorators = []
        for d in node.decorator_list:
            if isinstance(d, ast.Name):
                decorators.append(f"@{d.id}")
            elif isinstance(d, ast.Attribute):
                decorators.append(f"@{d.value.id}.{d.attr}")
            elif isinstance(d, ast.Call):
                if isinstance(d.func, ast.Attribute):
                    decorators.append(f"@{d.func.value.id}.{d.func.attr}(...)")
                elif isinstance(d.func, ast.Name):
                    decorators.append(f"@{d.func.id}(...)")
        return ", ".join(decorators) if decorators else "-"

    def _get_bases(self, node):
        """Mengambil parent class (Inheritance)"""
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(f"{b.value.id}.{b.attr}")
        return ", ".join(bases) if bases else "-"

    def _get_global_context(self, tree):
        imports, globals_vars = set(), set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split('.')[0])
                    if n.asname: imports.add(n.asname)
            elif isinstance(node, ast.ImportFrom):
                if node.module: imports.add(node.module.split('.')[0])
                for n in node.names:
                    if n.asname: imports.add(n.asname)
                    else: imports.add(n.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if not target.id.startswith('__'): globals_vars.add(target.id)
        return imports, globals_vars

    def _analyze_internals(self, node, global_imports, global_vars):
        used_imports, used_globals = set(), set()
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                if n.id in global_imports: used_imports.add(n.id)
                elif n.id in global_vars: used_globals.add(n.id)
        return sorted(list(used_imports)), sorted(list(used_globals))

    def _get_signature(self, node):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            method_str = ", ".join(methods[:5])
            if len(methods) > 5: method_str += f", +{len(methods)-5} more"
            return f"Methods: {method_str}"
        else:
            args = [arg.arg for arg in node.args.args]
            if node.args.vararg: args.append(f"*{node.args.vararg.arg}")
            if node.args.kwarg: args.append(f"**{node.args.kwarg.arg}")
            return f"({', '.join(args)})"

    def run_map(self):
        results = []
        print(f"🚀 Memulai Mapping Arsitektur V4 (GOD MODE) di: {self.target_path} ...")

        for root, dirs, files in os.walk(self.target_path):
            dirs[:] = [d for d in dirs if not self.is_excluded(os.path.join(root, d))]

            for file in files:
                full_path = os.path.join(root, file)
                if not file.endswith('.py') or self.is_excluded(full_path):
                    continue

                rel_path = os.path.relpath(full_path, self.target_path).replace('\\', '/')

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    try:
                        tree = ast.parse(content)
                    except SyntaxError:
                        results.append({
                            "File": rel_path, "Entity": "⚠️ SYNTAX ERR", "Type": "ERROR",
                            "LOC": 0, "Complexity": 0, "Decorators": "-", "Inheritance": "-",
                            "Signature": "-", "Imports": "-", "Globals": "-"
                        })
                        continue

                    global_imports, global_vars = self._get_global_context(tree)
                    definitions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]

                    if not definitions:
                        loc = content.count('\n') + 1
                        results.append({
                            "File": rel_path, "Entity": "(Script)", "Type": "📄 SCRIPT",
                            "LOC": loc, "Complexity": 0, "Decorators": "-", "Inheritance": "-",
                            "Signature": "-", "Imports": "-", "Globals": "Global Logic"
                        })
                        continue

                    for node in definitions:
                        is_async = isinstance(node, ast.AsyncFunctionDef)
                        is_class = isinstance(node, ast.ClassDef)
                        type_str = "🏛️ CLASS" if is_class else ("⚡ ASYNC" if is_async else "🔹 SYNC")

                        loc = self._get_loc(node)
                        complexity = self._get_complexity(node)
                        decorators = self._get_decorators(node)
                        bases = self._get_bases(node) if is_class else "-"

                        u_imp, u_glob = [], []
                        if not is_class:
                            u_imp, u_glob = self._analyze_internals(node, global_imports, global_vars)

                        results.append({
                            "File": rel_path,
                            "Entity": node.name,
                            "Type": type_str,
                            "LOC": loc,
                            "Complexity": complexity,
                            "Decorators": decorators,
                            "Inheritance": bases,
                            "Signature": self._get_signature(node),
                            "Imports": ", ".join(u_imp) if u_imp else "-",
                            "Globals": ", ".join(u_glob) if u_glob else "-"
                        })

                except Exception as e:
                    pass

        self._save_results(results)

    def _save_results(self, data):
        if not data:
            print("❌ Tidak ada data.")
            return

        if PANDAS_AVAILABLE:
            try:
                df = pd.DataFrame(data)
                cols = ["File", "Entity", "Type", "LOC", "Complexity", "Decorators", "Inheritance", "Signature", "Imports", "Globals"]
                df = df[cols]

                with pd.ExcelWriter(self.output_xlsx, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='ArchMap V4')
                print(f"\n✅ EXCEL GOD MODE SAVED: {os.path.abspath(self.output_xlsx)}")
            except Exception as e:
                print(f"\n⚠️ Fallback to CSV ({e})")
                self._save_csv(data)
        else:
            self._save_csv(data)

        self._save_markdown(data)

    def _save_csv(self, data):
        import csv
        with open(self.output_csv, 'w', newline='', encoding='utf-8') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        print(f"✅ CSV Saved: {os.path.abspath(self.output_csv)}")

    def _save_markdown(self, data):
        with open(self.output_md, "w", encoding="utf-8") as f:
            f.write("# 🗺️ FLOWORK ARCHITECTURE MAP V4 (GOD MODE)\n\n")
            f.write("| File | Entity | Type | LOC | Comp | Decorators | Inheritance | Signature | Imports |\n")
            f.write("|---|---|---|---|---|---|---|---|---|\n")

            for row in data:
                imp = row['Imports'][:30] + "..." if len(row['Imports']) > 30 else row['Imports']
                dec = row['Decorators'][:20] + "..." if len(row['Decorators']) > 20 else row['Decorators']

                line = f"| `{row['File']}` | **{row['Entity']}** | {row['Type']} | {row['LOC']} | {row['Complexity']} | `{dec}` | `{row['Inheritance']}` | `{row['Signature']}` | {imp} |"
                f.write(line + "\n")
        print(f"✅ Markdown Saved: {os.path.abspath(self.output_md)}")

if __name__ == "__main__":
    target_dir = r"C:\FLOWORK"
    if len(sys.argv) > 1: target_dir = sys.argv[1]
    mapper = ArchitectureMapperV4(target_dir)
    mapper.run_map()
