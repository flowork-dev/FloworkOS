########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\core\permission_hook.py total lines 42 
########################################################################

import sys
from flowork_kernel.kernel import Kernel
from flowork_kernel.exceptions import PermissionDeniedError
_kernel_instance = None
def get_kernel():
    global _kernel_instance
    if _kernel_instance is None:
        _kernel_instance = Kernel.instance
    return _kernel_instance
class PermissionHook:

    PROTECTED_MODULES = {
        "selenium": "web_scraping_advanced",
        "webdriver_manager": "web_scraping_advanced",
        "torch": "ai_local_models",
        "diffusers": "ai_local_models",
        "transformers": "ai_local_models",
        "llama_cpp": "ai_local_models",
        "moviepy": "video_processing",
    }
    def __init__(self):
        self._active = False
        kernel = get_kernel()
        if kernel:
            event_bus = kernel.get_service("event_bus", is_system_call=True)
            if event_bus:
                event_bus.subscribe("event_all_services_started", "PermissionHookActivator", self.activate)
    def activate(self, event_data=None):

        kernel = get_kernel()
        if kernel:
            kernel.write_to_log("PermissionHook: Activated (Open Core Mode - Checks Disabled).", "INFO")
        self._active = True
    def find_spec(self, fullname, path, target=None):

        return None
