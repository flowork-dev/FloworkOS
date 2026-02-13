########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\handle_get_apps_native.py total lines 74 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import asyncio
import json
import logging
from aiohttp import web

async def run(hub, request):
    """
    Menangani GET /api/v1/apps
    """
    try:
        if hasattr(hub, 'logger'):
            hub.logger.info("📡 [API] Processing GET /api/v1/apps")

        app_srv = hub.kernel.get_service("app_service")
        if not app_srv:
            if hasattr(hub, 'logger'):
                hub.logger.warning("⚠️ AppService not found in Kernel!")
            return web.json_response([])

        registry = {}
        try:
            if hasattr(app_srv, 'get_registry'):
                registry = app_srv.get_registry("apps")
                if asyncio.iscoroutine(registry):
                    registry = await registry
            else:
                hub.logger.error("❌ AppService has no 'get_registry' method!")
        except Exception as e:
            hub.logger.error(f"❌ Error getting app registry: {e}")
            return web.json_response([])

        if not registry:
            return web.json_response([])

        all_muscles = []
        for aid, info in registry.items():
            try:
                if not isinstance(info, dict): continue

                manifest = info.get("manifest", {})
                if not manifest: manifest = {}

                app_data = {
                    "id": aid,
                    "name": manifest.get("name", aid),
                    "manifest": manifest,
                    "icon_url": info.get("icon_url", ""),
                    "gui_url": f"/api/v1/muscle-assets/{aid}/assets/index.html",
                    "category": info.get("type", "app"),
                    "status": "active",
                    "services": info.get("services", [])
                }
                all_muscles.append(app_data)
            except Exception as item_err:
                hub.logger.error(f"⚠️ Error parsing app {aid}: {item_err}")
                continue

        if hasattr(hub, 'logger'):
            hub.logger.info(f"✅ [API] Returning {len(all_muscles)} apps to UI")

        return web.json_response(all_muscles)

    except Exception as e:
        error_msg = f"Critical Error in handle_get_apps_native: {str(e)}"
        if hasattr(hub, 'logger'):
            hub.logger.error(error_msg)

        return web.json_response([], status=200)
