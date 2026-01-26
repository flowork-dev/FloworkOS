########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\_load_api_routes.py total lines 40 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
from aiohttp import web

def run(hub):
    hub.app.router.add_get('/api/v1/apps', hub.handle_get_apps_native)
    hub.app.router.add_get('/api/v1/muscle-assets/{app_id}/assets/{filename:.*}', hub.handle_muscle_assets)
    hub.app.router.add_get('/api/v1/components/app/{app_id}/icon', hub.handle_legacy_icon)
    hub.app.router.add_get('/api/v1/user/preferences', lambda r: web.json_response({'status': 'success'}))
    hub.app.router.add_post('/api/v1/apps/execute/{app_id}/{action}', hub.handle_app_execute)
    hub.app.router.add_post('/api/v1/apps/execute/{app_id}', hub.handle_app_execute)

    hub.app.router.add_post('/api/connect/{service_name}/{action}', hub.dynamic_service_gateway)


    from .routes.filesystem_routes import FilesystemRoutes
    from .routes.engine_routes import EngineRoutes
    from .routes.preset_routes import PresetRoutes
    from .routes.ui_state_routes import UIStateRoutes
    from .routes.variable_routes import VariableRoutes

    all_rc = [FilesystemRoutes, EngineRoutes, PresetRoutes, UIStateRoutes, VariableRoutes]

    for rc in all_rc:
        try:
            inst = rc(hub)
            regs = inst.register_routes()
            for (route, hand) in regs.items():
                (m, p) = route.split(' ', 1)
                if p == '/api/v1/user/preferences':
                    continue
                hub.app.router.add_route(m, p, hand)
        except Exception as e:
            if hasattr(hub, 'logger'):
                hub.logger.error(f"Error loading routes from {rc}: {e}")
