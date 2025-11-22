########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\startup_service\startup_service.py total lines 155 
########################################################################

from ..base_service import BaseService
import time
import asyncio
from flowork_kernel.exceptions import (
    MandatoryUpdateRequiredError,
    PermissionDeniedError,
)
import os
class StartupService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        pass
    async def run_startup_sequence(self):

        try:
            self.logger("StartupService (Phase 1): Pre-flight checks...", "INFO")
            update_service = self.kernel.get_service(
                "update_service", is_system_call=True
            )
            if update_service:
                update_service.run_update_check()
            integrity_checker = self.kernel.get_service(
                "integrity_checker_service", is_system_call=True
            )
            if integrity_checker:
                integrity_checker.verify_core_files()
            self.logger(
                "StartupService (Phase 2): Starting all core and essential services...",
                "INFO",
            )
            essential_services_to_start = {
                "api_server_service": None,
                "module_manager_service": lambda s: s.discover_and_load_modules(),
                "plugin_manager_service": lambda s: s.discover_and_load_plugins(),
                "tools_manager_service": lambda s: s.discover_and_load_tools(),
                "scanner_manager_service": lambda s: s.discover_and_load_scanners(),
                "widget_manager_service": lambda s: s.discover_and_load_widgets(),
                "trigger_manager_service": lambda s: s.discover_and_load_triggers(),
                "preset_manager_service": lambda s: s.start(),
                "localization_manager": lambda s: s.load_all_languages(),
                "scheduler_manager_service": lambda s: s.start(),
                "gateway_connector_service": None,
            }
            for service_id, start_action in essential_services_to_start.items():
                try:
                    service_instance = self.kernel.get_service(
                        service_id, is_system_call=True
                    )
                    if service_instance:
                        if (
                            start_action is None
                            and hasattr(service_instance, "start")
                            and asyncio.iscoroutinefunction(service_instance.start)
                        ):
                            await service_instance.start()
                        elif (
                            start_action is None
                            and hasattr(service_instance, "start")
                            and not asyncio.iscoroutinefunction(service_instance.start)
                        ):
                            service_instance.start()
                        elif start_action:
                            start_action(service_instance)
                except Exception as e:
                    self.logger(
                        self.loc.get(
                            "log_startup_service_error", service_id=service_id, error=e
                        ),
                        "ERROR",
                    )
            self.logger(
                "StartupService (Phase 3): User identity and permission setup...",
                "INFO",
            )
            self._attempt_auto_login()
            license_manager = self.kernel.get_service(
                "license_manager_service", is_system_call=True
            )
            if license_manager:
                license_manager.verify_license_on_startup()
            permission_manager = self.kernel.get_service(
                "permission_manager_service", is_system_call=True
            )
            if permission_manager and license_manager:
                self.logger(self.loc.get("log_startup_inject_rules"), "INFO")
                permission_manager.load_rules_from_source(
                    license_manager.remote_permission_rules
                )
            self.logger(
                "StartupService (Phase 4): Starting remaining and gateway services...",
                "INFO",
            )
            remaining_services = [
                "trigger_manager_service",
            ]
            for service_id in remaining_services:
                try:
                    service_instance = self.kernel.get_service(
                        service_id, is_system_call=True
                    )
                    if service_instance and hasattr(service_instance, "start"):
                        service_instance.start()
                except PermissionDeniedError:
                    self.logger(
                        self.loc.get("log_startup_skip_service", service_id=service_id),
                        "WARN",
                    )
            self.logger(
                "StartupService: Activating background service plugins...", "INFO"
            )
            plugin_manager = self.kernel.get_service(
                "plugin_manager_service", is_system_call=True
            )
            if plugin_manager:
                for plugin_id, plugin_data in plugin_manager.loaded_plugins.items():
                    if plugin_data.get("manifest", {}).get("is_service"):
                        try:
                            plugin_manager.get_instance(plugin_id)
                        except PermissionDeniedError:
                            self.logger(
                                f"Skipped loading service plugin '{plugin_id}' due to license restrictions.",
                                "WARN",
                            )
            time.sleep(1)
            event_bus = self.kernel.get_service("event_bus", is_system_call=True)
            if event_bus:
                event_bus.publish("event_all_services_started", {})
            self.kernel.startup_complete = True
            self.logger(self.loc.get("log_startup_all_services_started"), "SUCCESS")
            return {"status": "complete"}
        except MandatoryUpdateRequiredError:
            raise
        except Exception as e:
            self.logger(self.loc.get("log_startup_critical_error", error=e), "CRITICAL")
            import traceback
            self.logger(traceback.format_exc(), "DEBUG")
            raise e
    def _attempt_auto_login(self):
        self.logger("StartupService: Attempting to load local user identity...", "INFO")
        state_manager = self.kernel.get_service("state_manager", is_system_call=True)
        if not state_manager:
            self.logger("StateManager not found. Cannot load user identity.", "WARN")
            self.kernel.current_user = None
            return
        self.logger("StartupService: No user identity loaded at startup. Waiting for GUI connection.", "INFO")
        self.kernel.current_user = None
        state_manager.delete("current_user_data")
        state_manager.delete("user_session_token")
