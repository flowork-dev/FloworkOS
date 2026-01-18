########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\variable_routes\register_routes.py total lines 13 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

def run(hub):
    return {
        'GET /api/v1/variables': hub.handle_get_variables,
        'GET /api/v1/variables/{variable_name}': hub.handle_get_single_variable,
        'PUT /api/v1/variables/{variable_name}': hub.handle_put_variable,
        'DELETE /api/v1/variables/{variable_name}': hub.handle_delete_variable
    }
