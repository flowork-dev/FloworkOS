########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\preset_routes\register_routes.py total lines 8 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

def run(hub):
    return {'GET /api/v1/presets': hub.handle_get_presets, 'GET /api/v1/presets/{preset_name}': hub.handle_get_preset_detail, 'POST /api/v1/presets': hub.handle_post_presets, 'DELETE /api/v1/presets/{preset_name}': hub.handle_delete_preset, 'GET /api/v1/presets/{preset_name}/versions': hub.handle_get_preset_versions, 'GET /api/v1/presets/{preset_name}/versions/{version_filename}': hub.handle_get_specific_preset_version, 'DELETE /api/v1/presets/{preset_name}/versions/{version_filename}': hub.handle_delete_preset_version, 'GET /api/v1/presets/{preset_name}/exists': hub.handle_check_preset_exists}
