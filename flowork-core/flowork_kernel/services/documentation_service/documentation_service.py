########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\documentation_service\documentation_service.py total lines 70 
########################################################################

import os
import subprocess
import threading
from ..base_service import BaseService
import platform
import signal
class DocumentationService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.process = None
        self.dev_mode = self.kernel.is_dev_mode
        if not self.dev_mode:
            self.logger("DocumentationService: 'devmode.on' not found. Documentation server will not be started.", "INFO")
    def start(self):

        if not self.dev_mode:
            return
        project_root = self.kernel.project_root_path
        if not os.path.exists(os.path.join(project_root, 'mkdocs.yml')):
            self.logger("DocumentationService: mkdocs.yml not found. Skipping server start.", "WARN")
            return
        thread = threading.Thread(target=self._run_mkdocs_serve, daemon=True)
        thread.start()
    def _run_mkdocs_serve(self):

        self.logger("DocumentationService: Starting 'mkdocs serve' in the background...", "INFO")
        command = ['poetry', 'run', 'mkdocs', 'serve']
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        try:
            self.process = subprocess.Popen(
                command,
                cwd=self.kernel.project_root_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                creationflags=creation_flags
            )
            self.logger(f"DocumentationService: 'mkdocs serve' is running with PID: {self.process.pid}", "SUCCESS")
        except FileNotFoundError:
            self.logger("DocumentationService: 'poetry' command not found. Make sure you are in a Poetry environment.", "CRITICAL")
        except Exception as e:
            self.logger(f"DocumentationService: Failed to start 'mkdocs serve': {e}", "CRITICAL")
    def stop(self):

        if self.process and self.process.poll() is None:
            self.logger(f"DocumentationService: Stopping 'mkdocs serve' process (PID: {self.process.pid})...", "INFO")
            try:
                if platform.system() == "Windows":
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=3)
                self.logger("DocumentationService: Process terminated gracefully.", "SUCCESS")
            except (ProcessLookupError, PermissionError):
                 self.logger("DocumentationService: Process was already gone before it could be stopped.", "INFO")
            except subprocess.TimeoutExpired:
                self.logger("DocumentationService: Process did not terminate in time, forcing kill.", "WARN")
                self.process.kill()
            except Exception as e:
                self.logger(f"DocumentationService: An unexpected error occurred during shutdown: {e}", "ERROR")
