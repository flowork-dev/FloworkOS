########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\function_runner_module\processor.py total lines 104 
########################################################################

import traceback
import sys
import io
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class FunctionRunnerModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self._ensure_icon()

    def _ensure_icon(self):
        pass

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        if mode == 'SIMULATE':
            status_updater("Simulating function execution...", "INFO")
            payload["_simulation_note"] = "Function Runner bypassed in simulation"
            return {"payload": payload, "output_name": "output"}

        code_to_run = config.get("function_code", "")
        timeout_sec = config.get("execution_timeout", 30)

        if not code_to_run:
            self.logger("No function code provided. Passing payload through.", "WARN")
            status_updater("Warning: No code to execute.", "WARN")
            return {"payload": payload, "output_name": "output"}

        status_updater("Executing custom Python script...", "INFO")

        class LoggerWrapper:
            def __init__(self, logger_func):
                self.logger_func = logger_func
            def write(self, text):
                if text.strip():
                    self.logger_func(text.strip(), "INFO")
            def flush(self):
                pass

        exec_globals = {
            '__builtins__': {
                'print': lambda *args, **kwargs: self.logger(" ".join(map(str, args)), "INFO"),
                'abs': abs, 'all': all, 'any': any, 'bin': bin, 'bool': bool, 'bytearray': bytearray,
                'bytes': bytes, 'callable': callable, 'chr': chr, 'complex': complex, 'delattr': delattr,
                'dict': dict, 'dir': dir, 'divmod': divmod, 'enumerate': enumerate, 'filter': filter,
                'float': float, 'format': format, 'frozenset': frozenset, 'getattr': getattr,
                'hasattr': hasattr, 'hash': hash, 'hex': hex, 'id': id, 'int': int, 'isinstance': isinstance,
                'issubclass': issubclass, 'iter': iter, 'len': len, 'list': list, 'map': map, 'max': max,
                'min': min, 'next': next, 'object': object, 'oct': oct, 'ord': ord, 'pow': pow,
                'property': property, 'range': range, 'repr': repr, 'reversed': reversed, 'round': round,
                'set': set, 'setattr': setattr, 'slice': slice, 'sorted': sorted, 'str': str,
                'sum': sum, 'super': super, 'tuple': tuple, 'type': type, 'zip': zip
            }
        }

        exec_locals = {
            "payload": payload,
            "log": self.logger,
            "status": status_updater, # Memberikan akses status update ke user script
            "kernel": self.kernel,
            "args": payload.get('data', {}).get('args', ()),
            "kwargs": payload.get('data', {}).get('kwargs', {})
        }

        try:
            exec(code_to_run, exec_globals, exec_locals)

            result_payload = exec_locals.get("payload", payload)

            status_updater("Function executed successfully.", "SUCCESS")
            return {"payload": result_payload, "output_name": "output"}

        except Exception as e:
            error_trace = traceback.format_exc()
            error_msg = f"Error in Function Runner:\n{error_trace}"

            self.logger(error_msg, "ERROR")
            status_updater("Script Execution Failed", "ERROR")

            payload['error'] = str(e)
            payload['error_trace'] = error_trace

            return {"payload": payload, "output_name": "error"}

    def get_data_preview(self, config: dict):
        code = config.get("function_code", "")
        preview_text = "No code defined"
        if code:
            lines = code.split('\n')
            preview_text = f"{len(lines)} lines of Python code ready."

        return [{
            "status": "ready",
            "message": preview_text,
            "details": {"lines": len(code.split('\n')) if code else 0}
        }]
