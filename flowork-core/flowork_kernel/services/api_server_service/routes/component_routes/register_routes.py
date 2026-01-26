########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\component_routes\register_routes.py total lines 46 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import mimetypes
import zipfile
import io
import base64
import shutil
import asyncio
from aiohttp import web
import threading


def run(hub):
    base_routes = ['GET /api/v1/{resource_type}', 'POST /api/v1/{resource_type}', 'GET /api/v1/{resource_type}/{item_id}', 'POST /api/v1/{resource_type}/install', 'PATCH /api/v1/{resource_type}/{item_id}/state', 'DELETE /api/v1/{resource_type}/{item_id}']
    routes = {}
    component_types = ['modules', 'plugins', 'tools', 'widgets', 'triggers', 'ai_providers', 'datasets', 'models']
    for route_pattern in base_routes:
        for comp_type in component_types:
            concrete_route = route_pattern.replace('{resource_type}', comp_type)
            (method, pattern) = concrete_route.split(' ', 1)
            if method == 'POST' and pattern.endswith('/install'):
                routes[concrete_route] = hub.handle_install_components
            elif method == 'POST' and (not pattern.endswith('/package')) and (not pattern.endswith('/install-package')):
                routes[concrete_route] = hub.handle_create_component
            elif 'state' in pattern:
                routes[concrete_route] = hub.handle_patch_component_state
            elif method == 'DELETE':
                routes[concrete_route] = hub.handle_delete_components
            else:
                routes[concrete_route] = hub.handle_get_components
    routes['GET /api/v1/ai_providers/services'] = hub.handle_get_ai_provider_services
    routes['GET /api/v1/components/{comp_type}/{item_id}/icon'] = hub.handle_get_component_icon
    routes['GET /api/v1/components/{comp_type}/{item_id}/assets/{filename:.*}'] = hub.handle_get_component_asset
    routes['GET /api/v1/widgets/{widget_id}/assets/{filename:.*}'] = hub.handle_get_widget_asset
    routes['POST /api/v1/components/package'] = hub.handle_package_component
    routes['POST /api/v1/components/install-package'] = hub.handle_install_package
    routes['POST /api/v1/components/run'] = hub.handle_run_component
    routes['POST /api/v1/components/custom/create'] = hub.handle_save_custom_component
    routes['POST /api/v1/apps/execute/{app_id}/{action}'] = hub.handle_app_execute_action
    return routes
