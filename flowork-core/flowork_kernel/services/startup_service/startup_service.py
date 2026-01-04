########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\startup_service\startup_service.py total lines 266 
########################################################################

from ..base_service import BaseService
import time
import asyncio
import subprocess
import sys
import os
from flowork_kernel.exceptions import (
    MandatoryUpdateRequiredError,
    PermissionDeniedError,
)

class StartupService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        pass

    async def run_startup_sequence(self):

        try:
            self.logger.info("StartupService (Phase 1): Pre-flight checks...")


            integrity_checker = self.kernel.get_service(
                "integrity_checker_service", is_system_call=True
            )
            if integrity_checker:
                integrity_checker.verify_core_files()

            self._auto_install_dependencies()

            self.logger.info(
                "StartupService (Phase 2): Starting all core and essential services..."
            )

            essential_services_to_start = {
                "api_server_service": None,
                "app_service": lambda s: s.start(), # [ADDED BY FOWORK DEV] Triggering unified scan
                "preset_manager_service": lambda s: s.start(),
                "localization_manager": lambda s: s.load_all_languages(),
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
                    self.logger.error(
                        self.loc.get(
                            "log_startup_service_error", service_id=service_id, error=e
                        )
                    )

            self.logger.info(
                "StartupService (Phase 3): User identity and permission setup..."
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
                self.logger.info(self.loc.get("log_startup_inject_rules"))
                permission_manager.load_rules_from_source(
                    license_manager.remote_permission_rules
                )

            self.logger.info(
                "StartupService (Phase 4): Starting remaining and gateway services..."
            )
            remaining_services = [
            ]
            for service_id in remaining_services:
                try:
                    service_instance = self.kernel.get_service(
                        service_id, is_system_call=True
                    )
                    if service_instance and hasattr(service_instance, "start"):
                        service_instance.start()
                except PermissionDeniedError:
                    self.logger.warning(
                        self.loc.get("log_startup_skip_service", service_id=service_id)
                    )

            self.logger.info(
                "StartupService: Activating background service plugins..."
            )
            app_manager = self.kernel.get_service(
                "app_service", is_system_call=True
            )
            if app_manager:
                plugins_found = getattr(app_manager, "loaded_plugins", {})
                self.logger.info(f"StartupService: Background scan found {len(plugins_found)} plugins.")

                for plugin_id, plugin_data in plugins_found.items():
                    if plugin_data.get("manifest", {}).get("is_service"):
                        try:
                            app_manager.get_instance("plugins", plugin_id)
                        except PermissionDeniedError:
                            self.logger.warning(
                                f"Skipped loading service plugin '{plugin_id}' due to license restrictions."
                            )
            time.sleep(1)
            event_bus = self.kernel.get_service("event_bus", is_system_call=True)
            if event_bus:
                event_bus.publish("event_all_services_started", {})
            self.kernel.startup_complete = True

            self.logger.info(self.loc.get("log_startup_all_services_started"))
            return {"status": "complete"}
        except MandatoryUpdateRequiredError:
            raise
        except Exception as e:
            self.logger.critical(self.loc.get("log_startup_critical_error", error=e))
            import traceback
            self.logger.debug(traceback.format_exc())
            raise e

    def _attempt_auto_login(self):
        self.logger.info("StartupService: Attempting to load local user identity...")
        state_manager = self.kernel.get_service("state_manager", is_system_call=True)
        if not state_manager:
            self.logger.warning("StateManager not found. Cannot load user identity.")
            self.kernel.current_user = None
            return
        self.logger.info("StartupService: No user identity loaded at startup. Waiting for GUI connection.")
        self.kernel.current_user = None
        state_manager.delete("current_user_data")
        state_manager.delete("user_session_token")

    def _get_real_root_path(self):
        """[MUTATED] Cerdas menentukan root path (Docker vs Local)"""
        if os.path.exists("/app/app"):
            return "/app/app"

        kernel_path = getattr(self.kernel, "project_root_path", None)
        if kernel_path:
            unified_app = os.path.join(kernel_path, "..", "app")
            if os.path.exists(unified_app):
                return os.path.abspath(unified_app)

            internal_app = os.path.join(kernel_path, "app")
            if os.path.exists(internal_app):
                return os.path.abspath(internal_app)

        return os.getcwd()

    def _auto_install_dependencies(self):
        root_path = self._get_real_root_path()

        self.logger.info(f"🔍 [Auto-Installer] Initializing Scan on App Root: {root_path}")

        max_retries = 5
        for i in range(max_retries):
            try:
                if os.path.exists(root_path) and len(os.listdir(root_path)) > 0:
                    self.logger.info(f"✅ [Auto-Installer] Volume mounted. Found app categories.")
                    break
            except: pass

            if i < max_retries - 1:
                self.logger.warning(f"⏳ [Auto-Installer] Waiting for file system mount... ({i+1}/{max_retries})")
                time.sleep(2)

        target_dirs = [
            'modules', 'plugins', 'tools', 'triggers',
            'widgets', 'ai_providers'
        ]

        install_count = 0

        for category in target_dirs:
            base_path = os.path.join(root_path, category)

            if not os.path.exists(base_path):
                continue

            try:
                items = os.listdir(base_path)
                self.logger.debug(f"[Auto-Installer] Category '{category}' found with {len(items)} items.")
            except Exception as e:
                self.logger.error(f"Error listing {base_path}: {e}")
                continue

            for item_name in items:
                item_path = os.path.join(base_path, item_name)

                if not os.path.isdir(item_path) or item_name.startswith('.') or item_name.startswith('__'):
                    continue

                req_file = os.path.join(item_path, "requirements.txt")
                flag_file = os.path.join(item_path, ".installed")

                if "golden_moment" in item_name:
                    if not os.path.exists(req_file):
                        self.logger.warning(f"🧐 [Auto-Installer] Golden Moment FOUND but requirements.txt MISSING!")
                    elif not os.path.exists(flag_file):
                        self.logger.info(f"🧐 [Auto-Installer] Golden Moment FOUND. Installing dependencies...")
                    else:
                        self.logger.info(f"🧐 [Auto-Installer] Golden Moment already installed.")

                if os.path.exists(req_file):
                    should_install = True

                    if os.path.exists(flag_file):
                        try:
                            req_mtime = os.path.getmtime(req_file)
                            flag_mtime = os.path.getmtime(flag_file)
                            if req_mtime < flag_mtime:
                                should_install = False
                        except:
                            should_install = True

                    if should_install:
                        self.logger.info(f"📦 [Auto-Installer] Installing dependencies for: {category}/{item_name}...")
                        try:
                            cmd = [
                                sys.executable, "-m", "pip", "install",
                                "-r", req_file,
                                "--disable-pip-version-check",
                                "--prefer-binary"
                            ]

                            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

                            if process.returncode == 0:
                                with open(flag_file, 'w') as f:
                                    f.write(f"Installed on {time.ctime()}")
                                self.logger.info(f"✅ [Auto-Installer] Success: {item_name}")
                                install_count += 1
                            else:
                                self.logger.error(f"❌ [Auto-Installer] FAILED: {item_name}\nLOG: {process.stdout[:500]}...")

                        except Exception as e:
                            self.logger.error(f"❌ [Auto-Installer] Unexpected Error {item_name}: {e}")

        if install_count > 0:
            self.logger.info(f"✨ [Auto-Installer] Complete. Installed dependencies for {install_count} components.")
        else:
            self.logger.info("⚡ [Auto-Installer] System up-to-date. No new component dependencies found.")
