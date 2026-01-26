########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\kernel.py total lines 13 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

try:
    from .kernel_logic import *
except ImportError as e:
    print("FATAL KERNEL ERROR: Could not load the compiled kernel logic (kernel_logic.kernel).")
    print(f"Ensure you have run the build_engine.py script. Details: {e}")
    import sys
    sys.exit(1)
