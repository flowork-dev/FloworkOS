########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\triggers\cron_trigger\processor.py total lines 47 
########################################################################

import datetime
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer

class CronTriggerModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "free"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        cron_string = config.get("cron_string", "*/5 * * * *")

        trigger_source = "scheduler"
        if mode == "SIMULATE" or kwargs.get("is_manual_run", False):
            status_updater(f"Manual Trigger fired (Schedule: {cron_string})", "INFO")
            trigger_source = "manual_override"
        else:
            status_updater(f"Scheduled Trigger fired: {cron_string}", "INFO")

        if 'data' not in payload:
            payload['data'] = {}

        payload['data']['trigger_info'] = {
            'type': 'cron',
            'schedule': cron_string,
            'source': trigger_source,
            'timestamp': datetime.datetime.now().isoformat()
        }

        self.logger(f"Cron Trigger active. Next node will execute.", "INFO")
        status_updater("Workflow started.", "SUCCESS")

        return {"payload": payload, "output_name": "output"}

    def get_data_preview(self, config: dict):
        return [{
            "status": "ready",
            "message": f"Schedule: {config.get('cron_string', 'Not set')}",
            "details": {"next_run": "Calculated by Scheduler Service"}
        }]
