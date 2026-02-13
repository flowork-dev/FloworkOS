########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\startup_service\run_startup_sequence.py total lines 78 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import time
import asyncio
import subprocess
import sys
import os
from flowork_kernel.exceptions import MandatoryUpdateRequiredError, PermissionDeniedError


async def run(hub):
    try:
        hub.logger.info('StartupService (Phase 1): Pre-flight checks...')
        integrity_checker = hub.kernel.get_service('integrity_checker_service', is_system_call=True)
        if integrity_checker:
            integrity_checker.verify_core_files()
        await hub.execute_async('_auto_install_dependencies')
        hub.logger.info('StartupService (Phase 2): Starting all core and essential services...')
        essential_services_to_start = {'api_server_service': None, 'app_service': lambda s: s.start(), 'preset_manager_service': lambda s: s.start(), 'localization_manager': lambda s: s.load_all_languages(), 'gateway_connector_service': None}
        for (service_id, start_action) in essential_services_to_start.items():
            try:
                service_instance = hub.kernel.get_service(service_id, is_system_call=True)
                if service_instance:
                    if start_action is None and hasattr(service_instance, 'start') and asyncio.iscoroutinefunction(service_instance.start):
                        await service_instance.start()
                    elif start_action is None and hasattr(service_instance, 'start') and (not asyncio.iscoroutinefunction(service_instance.start)):
                        service_instance.start()
                    elif start_action:
                        start_action(service_instance)
            except Exception as e:
                hub.logger.error(hub.loc.get('log_startup_service_error', service_id=service_id, error=e))
        hub.logger.info('StartupService (Phase 3): User identity and permission setup...')
        await hub.execute_async('_attempt_auto_login')
        license_manager = hub.kernel.get_service('license_manager_service', is_system_call=True)
        if license_manager:
            license_manager.verify_license_on_startup()
        permission_manager = hub.kernel.get_service('permission_manager_service', is_system_call=True)
        if permission_manager and license_manager:
            hub.logger.info(hub.loc.get('log_startup_inject_rules'))
            permission_manager.load_rules_from_source(license_manager.remote_permission_rules)
        hub.logger.info('StartupService (Phase 4): Starting remaining and gateway services...')
        remaining_services = []
        for service_id in remaining_services:
            try:
                service_instance = hub.kernel.get_service(service_id, is_system_call=True)
                if service_instance and hasattr(service_instance, 'start'):
                    service_instance.start()
            except PermissionDeniedError:
                hub.logger.warning(hub.loc.get('log_startup_skip_service', service_id=service_id))
        hub.logger.info('StartupService: Activating background service plugins...')
        app_manager = hub.kernel.get_service('app_service', is_system_call=True)
        if app_manager:
            plugins_found = getattr(app_manager, 'loaded_plugins', {})
            hub.logger.info(f'StartupService: Background scan found {len(plugins_found)} plugins.')
            for (plugin_id, plugin_data) in plugins_found.items():
                if plugin_data.get('manifest', {}).get('is_service'):
                    try:
                        app_manager.get_instance('plugins', plugin_id)
                    except PermissionDeniedError:
                        hub.logger.warning(f"Skipped loading service plugin '{plugin_id}' due to license restrictions.")
        time.sleep(1)
        event_bus = hub.kernel.get_service('event_bus', is_system_call=True)
        if event_bus:
            event_bus.publish('event_all_services_started', {})
        hub.kernel.startup_complete = True
        hub.logger.info(hub.loc.get('log_startup_all_services_started'))
        return {'status': 'complete'}
    except MandatoryUpdateRequiredError:
        raise
    except Exception as e:
        hub.logger.critical(hub.loc.get('log_startup_critical_error', error=e))
        import traceback
        hub.logger.debug(traceback.format_exc())
        raise e
