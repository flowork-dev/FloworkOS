########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_runtime_service\create_atomic_cell.py total lines 42 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os

def run(service, app_id, cell_name, code, *args, **kwargs):
    """
    Menulis Atomic Cell (.py) ke folder logic aplikasi tertentu.
    Mematuhi prinsip 1 File = 1 Fungsi.
    """
    try:
        app_service = service.kernel.get_service('app_service')
        if not app_service:
            return {"status": "error", "message": "AppService not found"}

        app_dir = os.path.join(app_service.base_app_path, app_id)
        logic_dir = os.path.join(app_dir, "logic")

        if not os.path.exists(logic_dir):
            os.makedirs(logic_dir)

        file_path = os.path.join(logic_dir, f"{cell_name}.py")

        final_code = code
        if "def run" not in code:

            indented_body = code.replace('\n', '\n    ')
            final_code = f"def run(app_context, *args, **kwargs):\n    {indented_body}"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_code)

        return {
            "status": "success",
            "message": f"Atomic Cell '{cell_name}' created in '{app_id}'",
            "path": file_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
