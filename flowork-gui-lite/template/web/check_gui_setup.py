########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\flowork-gui-lite\template\web\check_gui_setup.py total lines 121 
########################################################################

import os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OK_COLOR = "\033[92m"
ERROR_COLOR = "\033[91m"
WARN_COLOR = "\033[93m"
RESET_COLOR = "\033[0m"
def print_check(message, is_ok):
    """Prints a formatted check message."""
    if is_ok:
        print(f"{OK_COLOR}[OK]{RESET_COLOR}      {message}")
    else:
        print(f"{ERROR_COLOR}[ERROR]{RESET_COLOR}   {message}")
    return is_ok
def print_warning(message):
    print(f"{WARN_COLOR}[WARNING]{RESET_COLOR} {message}")
def check_rogue_main_js():
    """CHECK 1: The most likely culprit. Checks for a conflicting main.js in the /views folder."""
    print("\n--- 1. Pengecekan File Konflik ---")
    rogue_file_path = os.path.join(PROJECT_ROOT, "src", "views", "main.js")
    if os.path.exists(rogue_file_path):
        return not print_check(
            f"Ditemukan file konflik di 'src/views/main.js'. Ini HARUS di-rename atau dihapus.",
            False,
        )
    rogue_file_bak = os.path.join(PROJECT_ROOT, "src", "views", "main.js.LAMA")
    rogue_file_nonaktif = os.path.join(PROJECT_ROOT, "src", "views", "main.js.NONAKTIF")
    rogue_file_bak2 = os.path.join(PROJECT_ROOT, "src", "views", "main.js.BAK")
    if (
        os.path.exists(rogue_file_bak)
        or os.path.exists(rogue_file_nonaktif)
        or os.path.exists(rogue_file_bak2)
    ):
        print_warning(
            f"Ditemukan file 'main.js' yang sudah di-rename di 'src/views/'. Ini bagus, pastikan tidak ada file 'main.js' aktif di sana."
        )
    return print_check(
        "Tidak ada file 'main.js' yang konflik di folder 'src/views/'.", True
    )
def check_correct_main_js():
    """CHECK 2: Verifies that the correct main.js in /src has the essential lines."""
    print("\n--- 2. Pengecekan File 'src/main.js' ---")
    correct_main_path = os.path.join(PROJECT_ROOT, "src", "main.js")
    if not os.path.exists(correct_main_path):
        return not print_check(
            f"File utama '{correct_main_path}' tidak ditemukan!", False
        )
    with open(correct_main_path, "r", encoding="utf-8") as f:
        content = f.read()
    checks = {
        "app.use(pinia)": "'app.use(pinia)' ditemukan sebelum router dan mounting.",
        "app.use(router)": "'app.use(router)' ditemukan sebelum mounting.",
        "app.mount('
    }
    all_ok = True
    for line, message in checks.items():
        if line not in content:
            print_check(f"Baris penting '{line}' TIDAK DITEMUKAN.", False)
            all_ok = False
        else:
            print_check(message, True)
    return all_ok
def check_index_html():
    """CHECK 3: Verifies that index.html points to the correct main.js file."""
    print("\n--- 3. Pengecekan 'index.html' ---")
    index_path = os.path.join(PROJECT_ROOT, "index.html")
    if not os.path.exists(index_path):
        return not print_check(f"File 'index.html' tidak ditemukan!", False)
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    correct_script_tag = '<script type="module" src="/src/main.js"></script>'
    if correct_script_tag not in content:
        return not print_check(
            f"Tag <script> di 'index.html' salah! Seharusnya menunjuk ke '/src/main.js'.",
            False,
        )
    return print_check(
        "'index.html' sudah menunjuk ke '/src/main.js' dengan benar.", True
    )
def check_router_file():
    """CHECK 4: Verifies the router file doesn't import stores at the top level."""
    print("\n--- 4. Pengecekan 'src/router/index.js' ---")
    router_path = os.path.join(PROJECT_ROOT, "src", "router", "index.js")
    if not os.path.exists(router_path):
        return not print_check(f"File router '{router_path}' tidak ditemukan!", False)
    with open(router_path, "r", encoding="utf-8") as f:
        content = f.read()
    bad_import = "import { useAuthStore } from '@/store/auth'"
    if bad_import in content and not content.lstrip().startswith("//"):
        return not print_check(
            f"Ditemukan import 'useAuthStore' yang aktif. Ini harus dinonaktifkan (diberi comment).",
            False,
        )
    return print_check(
        "File router sudah bersih dari import store yang bermasalah.", True
    )
def main():
    """Runs all checks."""
    print("=== Menjalankan Diagnosa Setup FLOWORK GUI ===")
    results = [
        check_rogue_main_js(),
        check_correct_main_js(),
        check_index_html(),
        check_router_file(),
    ]
    print("\n--- KESIMPULAN ---")
    if all(results):
        print(
            f"{OK_COLOR}SEMUA PENGECEKAN BERHASIL!{RESET_COLOR} Setup project GUI lu sudah benar. Jika error masih ada, coba bersihkan cache browser."
        )
    else:
        print(
            f"{ERROR_COLOR}DITEMUKAN MASALAH KONFIGURASI!{RESET_COLOR} Silakan perbaiki [ERROR] yang ditandai di atas."
        )
if __name__ == "__main__":
    main()
