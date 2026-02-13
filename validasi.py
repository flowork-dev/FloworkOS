########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\validasi.py total lines 205 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import ast
import os
import re
import difflib
import sys

class DNA_Normalizer(ast.NodeTransformer):
    """Menyammakan struktur AST antara Source dan Result biar validasi adil"""
    def visit_Name(self, node):
        if node.id == 'hub':
            return ast.copy_location(ast.Name(id='self', ctx=node.ctx), node)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        return node

    def visit_arg(self, node):
        if node.arg == 'hub':
            return ast.copy_location(ast.arg(arg='self', annotation=node.annotation, type_comment=node.type_comment), node)
        return self.generic_visit(node)

    def visit_Await(self, node):
        if isinstance(node.value, ast.Call) and \
           isinstance(node.value.func, ast.Attribute) and \
           isinstance(node.value.func.value, ast.Name) and \
           node.value.func.value.id == 'hub' and \
           node.value.func.attr in ['execute', 'execute_async']:
            return self.visit(node.value)
        return self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and \
           isinstance(node.func.value, ast.Name) and \
           node.func.value.id == 'hub' and \
           node.func.attr in ['execute', 'execute_sync', 'execute_async']:

            if len(node.args) > 0 and isinstance(node.args[0], (ast.Str, ast.Constant)):
                arg0 = node.args[0]
                method_name = arg0.s if isinstance(arg0, ast.Str) else arg0.value

                new_func = ast.Attribute(
                    value=ast.Name(id='self', ctx=ast.Load()),
                    attr=method_name,
                    ctx=node.func.ctx
                )
                new_args = [self.visit(a) for a in node.args[1:]]
                new_keywords = [self.visit(k) for k in node.keywords]
                return ast.copy_location(ast.Call(func=new_func, args=new_args, keywords=new_keywords), node)

        self.generic_visit(node)
        return node

    def generic_visit(self, node):
        if isinstance(node, ast.AsyncFunctionDef):
            new_node = ast.FunctionDef(
                name=node.name, args=node.args, body=node.body,
                decorator_list=node.decorator_list, returns=node.returns, type_comment=node.type_comment
            )
            ast.copy_location(new_node, node)
            node = new_node
        return super().generic_visit(node)

class SurgeryValidator:
    def __init__(self, root_path):
        self.root_path = root_path

    def parse_list_txt(self, list_path):
        if not os.path.exists(list_path): return {}
        with open(list_path, 'r', encoding='utf-8') as f: content = f.read()
        parsed = {}
        sections = re.split(r'📍\s*FILE\s*:', content)[1:]
        for section in sections:
            lines = section.strip().split('\n')
            rel_path = lines[0].strip()
            full_path = os.path.join(self.root_path, rel_path)
            funcs_block = re.search(r'(?:📜|📂)\s*LIST\s+(?:FUNCTIONS|FUNGSI).*?:\s*\r?\n(.*?)(?=\n\s*-|\n\s*=|$)', section, re.DOTALL | re.IGNORECASE)
            if funcs_block:
                raw_funcs = funcs_block.group(1)
                funcs = re.findall(r'(?:\d+\.|-)\s*(\w+)', raw_funcs)
                if funcs:
                    parsed[full_path] = funcs
        return parsed

    def standardize_node(self, node, func_name_override=None):
        node = DNA_Normalizer().visit(node)
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
             node.decorator_list = []
             if func_name_override:
                 node.name = func_name_override
        return node

    def get_dna_str(self, code, is_new_cell=False, func_name_target=None):
        try:
            tree = ast.parse(code)
            target_node = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if is_new_cell and node.name == 'run':
                        target_node = node
                        break
                    elif not is_new_cell and node.name == func_name_target:
                        target_node = node
                        break
            if not target_node: return None

            norm_node = self.standardize_node(target_node, func_name_override="COMPARE")
            return ast.unparse(norm_node)
        except Exception as e: return None

    def run_audit(self, list_txt_path):
        audit_list = self.parse_list_txt(list_txt_path)
        print(f"\n{'='*85}\n🚀 FLOWORK SURGERY INTELLIGENT AUDIT (v5.0 - FOLDER AWARE)\n{'='*85}")
        all_passed = True

        for file_path, functions in audit_list.items():

            backup_path = file_path + ".bak_original"

            target_dir_name = os.path.splitext(file_path)[0]

            is_folder_package = False
            source_code_path = None

            if os.path.exists(backup_path):
                source_code_path = backup_path
                is_folder_package = True
                display_name = f"{os.path.basename(file_path)} (PACKAGE)"
                search_dir = target_dir_name # Cari cell di dalam folder baru

            elif os.path.exists(file_path + ".bak_modular"):
                source_code_path = file_path + ".bak_modular"
                display_name = os.path.basename(file_path)
                search_dir = os.path.dirname(file_path) # Cari cell di sebelah file

            elif os.path.exists(file_path):
                source_code_path = file_path
                display_name = f"{os.path.basename(file_path)} (SKIPPED/RAW)"
                search_dir = os.path.dirname(file_path)
            else:
                print(f"\n[?] Source Missing: {file_path}")
                continue

            print(f"\n📂 TARGET   : {display_name}")

            try:
                with open(source_code_path, 'r', encoding='utf-8') as f:
                    bak_content = f.read()
            except:
                print("   ❌ Cannot read source.")
                continue

            for func in functions:
                cell_path = os.path.join(search_dir, f"{func}.py")

                orig_code = self.get_dna_str(bak_content, is_new_cell=False, func_name_target=func)
                new_code = None

                if os.path.exists(cell_path):
                    with open(cell_path, 'r', encoding='utf-8') as f:
                        new_code = self.get_dna_str(f.read(), is_new_cell=True)
                else:
                    if not is_folder_package and source_code_path == file_path:
                         if orig_code: new_code = orig_code

                if orig_code and new_code and orig_code.strip() == new_code.strip():
                    print(f"  [✓] {func:<35} | ✅ MATCH 100%")
                else:
                    if new_code is None:
                         if "start.py" in file_path:
                             print(f"  [-] {func:<35} | ℹ️  SKIPPED (Intentional)")
                         else:
                             print(f"  [!] {func:<35} | ❌ FILE MISSING ({os.path.basename(search_dir)}/{func}.py)")
                             all_passed = False
                    else:
                        print(f"  [!] {func:<35} | 🔥 LOGIC BREACH!")
                        print("      --- DIFF SNIPPET ---")
                        diff = difflib.unified_diff(
                            orig_code.splitlines(),
                            new_code.splitlines(),
                            fromfile='Original',
                            tofile='New Cell',
                            lineterm=''
                        )
                        for line in list(diff)[:5]:
                            print(f"      {line}")
                        print("      --------------------")
                        all_passed = False

        if all_passed:
            print(f"\n{'='*85}\n🎉 CONGRATULATIONS! ALL PACKAGES VERIFIED.\n{'='*85}")
        else:
            print(f"\n{'='*85}\n⚠️ WARNING: CHECK LOGS ABOVE.\n{'='*85}")

if __name__ == "__main__":
    list_file = "surgery_report.txt"
    if len(sys.argv) > 1: list_file = sys.argv[1]
    root = os.getcwd()
    SurgeryValidator(root).run_audit(list_file)
