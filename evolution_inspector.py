########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\evolution_inspector.py total lines 140 
########################################################################

import os
import ast
import fnmatch
import csv # [English Note] Added for CSV export functionality

MAX_LINES_LIMIT = 100
MAX_IMPORTS_LIMIT = 8
MAX_FUNCTIONS_LIMIT = 5 # [English Note] Nano-modular limit: one file should be lean
PROJECT_ROOT = os.getcwd()

EXCLUDE_DIRS = [
    '.venv', 'venv', 'cache', 'unsloth_compiled_cache', '.github', 'vendor',
    'temp_research_audio', 'llama.cpp', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'nodejs', 'backup', 'data', 'logs', '_logs',
    'ai_models', '.vscode', 'assets', 'capsules', 'flowork-cloud', 'flowork-gui',
    'formatters', 'scanners', 'triggers', 'tools', 'migrations', 'modules',
    'plugins', 'widgets', 'locales'
]

EXCLUDE_FILES = [
    'backup.py', 'pre_launcher.pid', '5-upload_momod_gui.bat',
    '6-upload_flowork_gui.bat', '7-upload-docs.bat', '8.publish.bat',
    '9.upload_all_project.bat', '10.BACKUPENGINE.bat', '11.BACKUPGUI.bat',
    'dump.rdb', '.dockerignore', '.gitignore', 'BACKUP_FOR_GEMINI.txt',
    'evolution_inspector.py'
]

class ModularityVisitor(ast.NodeVisitor):
    """[English Note] Analyzing Python Abstract Syntax Tree for decoupling metrics."""
    def __init__(self):
        self.import_count = 0
        self.class_count = 0
        self.function_count = 0
        self.items = [] # [English Note] List to store 'Class: Name' or 'Func: Name' strings

    def visit_Import(self, node):
        self.import_count += len(node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.import_count += len(node.names)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.class_count += 1
        self.items.append(f"Class: {node.name}") # [English Note] Capturing class name for CSV list
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.function_count += 1
        self.items.append(f"Func: {node.name}") # [English Note] Capturing function name for CSV list
        self.generic_visit(node)

def run_audit():

    output_filename = "nano_evolution_plan.csv" # [English Note] Target CSV file name
    total_scanned = 0
    titans_found = 0

    with open(output_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["FILE_PATH", "TOTAL", "BREAKDOWN", "SERVICE_LIST"])

        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if not file.endswith(".py") or file in EXCLUDE_FILES:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/") # [English Note] Standardizing paths

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = content.splitlines()
                        line_count = len(lines)

                    tree = ast.parse(content)
                    visitor = ModularityVisitor()
                    visitor.visit(tree)

                    reasons = []
                    is_bad = False

                    if line_count > MAX_LINES_LIMIT:
                        is_bad = True
                        reasons.append(f"Oversized ({line_count} lines)")

                    if visitor.import_count > MAX_IMPORTS_LIMIT:
                        is_bad = True
                        reasons.append(f"Tight Coupling ({visitor.import_count} imports)")

                    if visitor.class_count > 1:
                        is_bad = True
                        reasons.append(f"Multi-Flow ({visitor.class_count} classes)")

                    if visitor.function_count > MAX_FUNCTIONS_LIMIT:
                        is_bad = True
                        reasons.append(f"Fat Logic ({visitor.function_count} functions)")

                    if is_bad:
                        titans_found += 1

                    total_items = len(visitor.items)
                    breakdown = f"[C:{visitor.class_count}, F:{visitor.function_count}]"
                    service_list_str = ", ".join(visitor.items)

                    writer.writerow([rel_path, total_items, breakdown, service_list_str])


                    total_scanned += 1

                except Exception:
                    pass

    print("\n" + "="*90)
    print(f"✅ AUDIT SELESAI! Hasilnya udah ditaruh di: {output_filename}")
    print(f"Total Logic Files Scanned : {total_scanned}")
    print(f"Monolithic Files Found    : {titans_found}")

    if total_scanned > 0:
        readiness = ((total_scanned - titans_found) / total_scanned) * 100
        print(f"Evolution Readiness Index : {readiness:.1f}%")

        if readiness < 80:
            print("\n[ADVICE] Kode Core masih banyak yang 'sticky'. Segera pecah logic yang kegedean ke /app.")
        else:
            print("\n[SUCCESS] Kode udah lean dan siap buat evolusi AI!")
    print("="*90)

if __name__ == "__main__":
    run_audit()
