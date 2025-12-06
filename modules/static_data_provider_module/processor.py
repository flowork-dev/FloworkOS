########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\static_data_provider_module\processor.py total lines 102 
########################################################################

import json
from flowork_kernel.api_contract import (
    BaseModule,
    IExecutable,
    IDataPreviewer,
    IDynamicOutputSchema,
    IDynamicPorts,
)

class StaticDataProviderModule(
    BaseModule, IExecutable, IDataPreviewer, IDynamicOutputSchema, IDynamicPorts
):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)

    def execute(self, payload, config, status_updater, mode="EXECUTE", **kwargs):
        if mode == "SIMULATE":
            status_updater("Simulating data injection...", "INFO")
        else:
            status_updater("Injecting static data...", "INFO")

        variables_to_set = config.get("variables_to_set", [])
        output_data = {}
        log_lines = ["Injecting Data:"]

        if not variables_to_set:
            status_updater("No variables configured to inject.", "WARN")
        else:
            for var_item in variables_to_set:
                var_name = var_item.get("name")
                var_value = var_item.get("value")

                if var_name:

                    output_data[var_name] = var_value
                    preview_val = str(var_value)[:50] + "..." if len(str(var_value)) > 50 else str(var_value)
                    log_lines.append(f"  + {var_name}: {preview_val}")

        if isinstance(payload, dict):
            if "data" not in payload or not isinstance(payload["data"], dict):
                payload["data"] = {}
            payload["data"].update(output_data)
        else:
            payload = {"data": output_data, "history": []}

        if len(log_lines) > 1:
            self.logger("\n".join(log_lines), "INFO")

        status_updater(f"Injected {len(output_data)} variables.", "SUCCESS")

        final_payload = {"payload": payload}

        final_payload["output_name"] = "success"

        return final_payload

    def get_dynamic_output_schema(self, config):
        schema = []
        variables = config.get("variables_to_set", [])
        for var in variables:
            var_name = var.get("name")
            if var_name:
                schema.append(
                    {
                        "name": f"data.{var_name}",
                        "type": "string", # Defaulting to string for schema description
                        "description": f"Static value: {str(var.get('value'))[:30]}",
                    }
                )
        return schema

    def get_dynamic_ports(self, config):
        return [
            {"name": "success", "display_name": "Success"},
            {"name": "error", "display_name": "Error"}
        ]

    def get_data_preview(self, config: dict):
        variables_to_set = config.get("variables_to_set", [])
        if not variables_to_set:
             return [{"status": "empty", "message": "No variables set"}]

        preview_data = {
            var.get("name"): var.get("value")
            for var in variables_to_set
            if var.get("name")
        }

        return [{
            "status": "ready",
            "message": f"Prepared {len(preview_data)} vars",
            "details": preview_data
        }]
