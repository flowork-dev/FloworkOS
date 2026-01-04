########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\execution\RetryHandler.py total lines 35 
########################################################################

import time
class RetryHandler:

    def __init__(self, kernel, core_executor_func):

        self.kernel = kernel
        self.loc = self.kernel.get_service("localization_manager")
        self.core_executor_func = core_executor_func
    def execute_with_retries(self, payload: dict, config: dict, node_info: dict, context_id: str, mode: str):

        retry_attempts = config.get('retry_attempts', 0)
        retry_delay = config.get('retry_delay_seconds', 5)
        node_name = node_info.get("name", "[Unnamed]")
        last_exception = None
        for attempt in range(retry_attempts + 1):
            if self.kernel.get_service("workflow_executor_service")._stop_event.is_set():
                self.kernel.write_to_log(f"Retry for node '{node_name}' cancelled by user.", "WARN")
                break
            if attempt > 0:
                self.kernel.write_to_log(
                    f"Node '{node_name}' failed. Retrying in {retry_delay}s... (Attempt {attempt}/{retry_attempts})", "WARN"
                )
                time.sleep(retry_delay)
            result = self.core_executor_func(payload, config, node_info, context_id, mode)
            if not isinstance(result, Exception):
                return result
            last_exception = result
        self.kernel.write_to_log(f"Node '{node_name}' failed after all {retry_attempts} retry attempts.", "ERROR")
        return last_exception
