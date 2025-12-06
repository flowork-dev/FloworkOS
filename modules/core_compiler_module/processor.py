########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\core_compiler_module\processor.py total lines 143 
########################################################################

import os
import json
import re
import shutil
import time
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class CoreCompilerModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.core_services_path = os.path.join(self.kernel.project_root_path, "core_services")
        self.generated_services_path = os.path.join(self.kernel.project_root_path, "generated_services")

    def _sanitize_for_method_name(self, name):
        """Mengubah nama node menjadi format method python yang valid (snake_case)."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub(r'[\s-]+', '_', s1).lower()

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        clean_build = config.get("clean_build", False)
        verbose = config.get("verbose_log", True)

        status_updater("Initializing Core Service compilation...", "INFO")

        if clean_build:
            if os.path.exists(self.generated_services_path):
                status_updater("Cleaning old generated services...", "INFO")
                try:
                    shutil.rmtree(self.generated_services_path)
                    time.sleep(0.5) # Memberi waktu OS untuk release file lock
                except Exception as e:
                    self.logger(f"Clean build failed: {e}", "WARN")

        os.makedirs(self.generated_services_path, exist_ok=True)

        root_init_path = os.path.join(self.generated_services_path, "__init__.py")
        if not os.path.exists(root_init_path):
            with open(root_init_path, 'w') as f:
                pass

        if not os.path.exists(self.core_services_path):
            return {"payload": {"error": f"Path not found: {self.core_services_path}"}, "output_name": "error"}

        compiled_count = 0
        errors = []

        files = [f for f in os.listdir(self.core_services_path) if f.endswith(".flowork")]
        total_files = len(files)

        status_updater(f"Found {total_files} service definitions.", "INFO")

        for idx, filename in enumerate(files):
            try:
                service_id = filename.replace(".flowork", "")

                if verbose:
                    status_updater(f"Compiling ({idx+1}/{total_files}): {service_id}", "INFO")

                service_dir = os.path.join(self.generated_services_path, f"{service_id}_service")
                os.makedirs(service_dir, exist_ok=True)

                sub_init_path = os.path.join(service_dir, "__init__.py")
                if not os.path.exists(sub_init_path):
                     with open(sub_init_path, 'w') as f:
                        pass

                service_file_path = os.path.join(service_dir, "service.py")
                preset_path_rel = os.path.join("core_services", filename).replace("\\", "/")
                class_name = "".join(word.capitalize() for word in service_id.split('_')) + "Service"

                with open(os.path.join(self.core_services_path, filename), 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)

                nodes = {node['id']: node for node in workflow_data.get('nodes', [])}
                connections = workflow_data.get('connections', [])

                all_node_ids = set(nodes.keys())
                nodes_with_incoming = set(conn['to'] for conn in connections)
                start_node_ids = all_node_ids - nodes_with_incoming

                code_lines = [
                    "from flowork_kernel.kernel_logic import ServiceWorkflowProxy",
                    "from flowork_kernel.services.base_service import BaseService",
                    "",
                    f"class {class_name}(BaseService):",
                    "    def __init__(self, kernel, service_id: str):",
                    "        super().__init__(kernel, service_id)",
                    f"        self.proxy = ServiceWorkflowProxy(kernel, service_id, \"{preset_path_rel}\")",
                    ""
                ]

                if not start_node_ids:
                    self.logger(f"WARNING: No start nodes found in {filename}. Service will have no methods.", "WARN")
                else:
                    for start_node_id in start_node_ids:
                        raw_name = nodes[start_node_id].get('name', 'unknown_method')
                        method_name = self._sanitize_for_method_name(raw_name)

                        code_lines.append(f"    def {method_name}(self, *args, **kwargs):")
                        code_lines.append(f"        return self.proxy.{method_name}(*args, **kwargs)")
                        code_lines.append("")

                with open(service_file_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(code_lines))

                compiled_count += 1

            except Exception as e:
                err_msg = f"Failed to process {filename}: {str(e)}"
                self.logger(err_msg, "ERROR")
                errors.append(err_msg)

        if errors:
            status_updater(f"Completed with {len(errors)} errors.", "WARN")
            return {
                "payload": {
                    "status": "partial_success",
                    "compiled": compiled_count,
                    "errors": errors
                },
                "output_name": "success" # Atau 'error' tergantung kebijakan strictness Anda
            }
        else:
            status_updater(f"Successfully compiled {compiled_count} services.", "SUCCESS")
            return {
                "payload": {
                    "status": "success",
                    "compiled": compiled_count
                },
                "output_name": "success"
            }

    def get_data_preview(self, config: dict):
        return [{'status': 'preview_not_available', 'reason': 'System compiler output is internal code structure.'}]
