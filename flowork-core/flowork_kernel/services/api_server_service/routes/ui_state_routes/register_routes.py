########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\ui_state_routes\register_routes.py total lines 11 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import threading


def run(hub):
    return {'GET /api/v1/uistate/dashboards/{tab_id}': hub.get_dashboard_state, 'POST /api/v1/uistate/dashboards/{tab_id}': hub.set_dashboard_state, 'GET /api/v1/uistate/session/tabs': hub.get_session_tabs, 'POST /api/v1/uistate/session/tabs': hub.set_session_tabs, 'GET /api/v1/uistate/generic/{key:.*}': hub.get_generic_state, 'POST /api/v1/uistate/generic/{key:.*}': hub.set_generic_state, 'DELETE /api/v1/uistate/generic/{key:.*}': hub.delete_generic_state}
