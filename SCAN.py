########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\SCAN.py total lines 219 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import ast
import os
import sys
from datetime import datetime

class SurgeonScanner:
    def __init__(self, target_paths):
        self.target_paths = target_paths
        self.output_report = "laporan_bedah_final.txt"

        self.exclude_dirs = {
            '.venv', 'venv', '.github', 'vendor', '__pycache__',
            '.pytest_cache', '.git', '.idea', '.vscode', 'migrations',
            'node_modules', '__pycache__'
        }

        self.allow_list = {
            'models.py', 'config.py', 'urls.py', 'wsgi.py', 'manage.py', 'conftest.py'
        }

    def run_scan(self):
        with open(self.output_report, "w", encoding="utf-8") as report:
            time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            header = "\n" + "="*100 + "\n"
            header += f"{'🕵️ SURGEON SCANNER - DETEKSI MONOLITH & HUB LEGACY':^100}\n"
            header += f"{'Kriteria: File > 1 Fungsi Utama OR __init__.py dengan Logika':^100}\n"
            header += f"{f'Generated on: {time_now}':^100}\n"
            header += "="*100 + "\n"

            print(header)
            report.write(header)

            violation_count = 0

            for path in self.target_paths:
                abs_target = os.path.abspath(path)
                if not os.path.exists(abs_target): continue

                print(f"📡 Scanning Sector: {abs_target}...\n")

                for root, dirs, files in os.walk(abs_target):
                    dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

                    for file in files:
                        if file.endswith(".py") and file not in self.allow_list:
                            full_path = os.path.join(root, file)
                            is_hit = self.analyze_file(full_path, report)
                            if is_hit:
                                violation_count += 1

            footer = "\n" + "="*100 + "\n"
            footer += f"🛑 TOTAL PASIEN YANG HARUS DIBEDAH: {violation_count}\n"
            footer += "="*100 + "\n"
            print(footer)
            report.write(footer)
            print(f"📄 Laporan Bedah tersimpan di: {os.path.abspath(self.output_report)}")

    def _get_global_context(self, tree):
        """Mendeteksi Import Global & Variabel Global di file"""
        imports = set()
        globals_vars = set()

        for node in tree.body:
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split('.')[0])
                    if n.asname: imports.add(n.asname)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
                for n in node.names:
                    if n.asname: imports.add(n.asname)
                    else: imports.add(n.name)

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if not target.id.startswith('__'):
                            globals_vars.add(target.id)

        return imports, globals_vars

    def _analyze_function_internals(self, func_node, global_imports, global_vars):
        """Menganalisa dependency dalam fungsi"""
        used_imports = set()
        used_globals = set()
        local_vars = set()

        for node in ast.walk(func_node):
            if isinstance(node, ast.Name):
                name = node.id
                if isinstance(node.ctx, ast.Load):
                    if name in global_imports:
                        used_imports.add(name)
                    elif name in global_vars:
                        used_globals.add(name)
                elif isinstance(node.ctx, ast.Store):
                    local_vars.add(name)

        return sorted(list(used_imports)), sorted(list(used_globals)), sorted(list(local_vars))

    def _get_args(self, node):
        args = []
        for arg in node.args.args:
            anot = ""
            if arg.annotation:
                try:
                    if hasattr(ast, 'unparse'): anot = f": {ast.unparse(arg.annotation)}"
                except: pass
            args.append(f"{arg.arg}{anot}")

        if node.args.vararg: args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg: args.append(f"**{node.args.kwarg.arg}")
        return ", ".join(args)

    def analyze_file(self, file_path, report_handle):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)

            definitions = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    definitions.append(node)

            filename = os.path.basename(file_path)

            if filename == "__init__.py" and len(definitions) == 0:
                return False

            if filename != "__init__.py" and len(definitions) <= 1:
                return False


            global_imports, global_vars = self._get_global_context(tree)

            status_label = "LEGACY HUB / ROUTER" if filename == "__init__.py" else "MONOLITH FILE"

            out = "\n" + "-"*100 + "\n"
            out += f"🚨 PASIEN: {file_path}\n"
            out += f"🏷️  STATUS: {status_label}\n"
            out += f"📊 BEBAN : {len(definitions)} Fungsi/Class Utama (Perlu dipecah)\n"
            out += f"📊 PECAH FILE INI MENJADI  : {len(definitions)}\n"
            out += f"Prinsip Utama \n\n"
            out += f"1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.\n"
            out += f"2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).\n"
            out += f"3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.\n"
            out += f"4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.\n\n"
            out += f"Instruksi Kerja (The Hub):\n\n"
            out += f"Ubah file target menjadi folder package dengan __init__.py.\n"
            out += f"Gunakan importlib untuk loading dinamis.\n"
            out += f"PENTING: Hub wajib mendukung Positional Arguments agar panggilannya identik. Gunakan signature: async def execute(self, cell_name, args, kwargs).\n\n"
            out += f"Instruksi Kerja (Atomic Cells):\n\n"
            out += f"Pecah fungsi berikut menjadi file mandiri: [DAFTAR FUNGSI DI SINI]\n"
            out += f"Entry Point Wajib: Gunakan async def run(hub, args, kwargs).\n"
            out += f"Transplantasi Kode 1:1: Ambil isi batang tubuh (body) fungsi asli dan tempel langsung ke dalam run.\n"
            out += f"Variable Mapping: - Ubah referensi global (seperti APP_ID, sio, logger) menjadi hub.APP_ID, hub.sio, hub.logger.\n"
            out += f"Ubah pemanggilan fungsi internal (seperti await process_action(...)) menjadi await hub.execute(process_action, ...) dengan urutan argumen yang sama persis.\n"
            out += f"PERINGATAN KERAS:\n\n"
            out += f"Gunakan metode penguapan (Transplantasi Kode). Jangan menulis ulang (rewrite). Ambil isi fungsi X dari baris A sampai B, lalu tempel ke fungsi run() di file baru. Jika saya menemukan satu variabel saja yang namanya berubah, satu pesan log yang dipotong, atau satu logika 'if' yang lu optimasi, kerjaan lu GAGAL dan akan ditolak oleh SurgeryValidator V3.5.\n"
            out += "-"*100 + "\n"

            for i, node in enumerate(definitions, 1):
                name = node.name
                is_class = isinstance(node, ast.ClassDef)

                is_async = isinstance(node, ast.AsyncFunctionDef)
                type_icon = "🏛️ CLASS" if is_class else ("⚡ ASYNC" if is_async else "🔹 SYNC")

                args_str = "..."
                used_imports, used_globals, local_vars = [], [], []

                if not is_class:
                    args_str = self._get_args(node)
                    used_imports, used_globals, local_vars = self._analyze_function_internals(node, global_imports, global_vars)
                else:
                    method_names = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    local_vars = method_names

                out += f"\n   ✂️  CANDIDATE {i}: {name}\n"
                out += f"       📝 Type       : {type_icon}\n"

                if not is_class:
                    out += f"       📥 Params     : ({args_str})\n"

                    if used_imports:
                        out += f"       📦 IMPORTS    : {', '.join(used_imports)}\n"
                        out += f"                       (👉 Wajib copy import ini ke file baru)\n"

                    if used_globals:
                        out += f"       ⚠️ GLOBAL VARS: {', '.join(used_globals)}\n"
                        out += f"                       (👉 PENTING: Fungsi ini baca variabel global file asli)\n"
                else:
                    out += f"       🔧 Methods    : {', '.join(local_vars)}\n"

            out += "\n"
            print(out, end='')
            report_handle.write(out)
            return True

        except Exception as e:
            return False

if __name__ == "__main__":
    target_sector = r"C:\FLOWORK\flowork-gateway"

    paths_to_scan = [target_sector]
    if len(sys.argv) > 1:
        paths_to_scan = sys.argv[1:]

    scanner = SurgeonScanner(paths_to_scan)
    scanner.run_scan()
