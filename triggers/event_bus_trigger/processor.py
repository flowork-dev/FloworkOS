########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\triggers\event_bus_trigger\processor.py total lines 79 
########################################################################

import datetime
import uuid
from flowork_kernel.api_contract import BaseModule, IExecutable, BaseTriggerListener, IDataPreviewer

class EventBusListener(BaseTriggerListener):

    def __init__(self, trigger_id, config, services, **kwargs):
        super().__init__(trigger_id, config, services, **kwargs)
        self.event_name = self.config.get("event_name_to_listen")

    def start(self):
        if not self.event_name:
            self.logger(f"Event Bus Trigger '{self.rule_id}' failed: Event name is missing.", "ERROR")
            return

        self.event_bus.subscribe(
            event_name=self.event_name,
            subscriber_id=f"trigger_listener::{self.rule_id}",
            callback=self.on_event_received
        )
        self.is_running = True
        self.logger(f"Listening for event: '{self.event_name}' (Rule: {self.rule_id})", "INFO")

    def on_event_received(self, event_data):
        self._on_event(event_data)

    def stop(self):
        if self.is_running and self.event_name:
            self.event_bus.unsubscribe(self.event_name, f"trigger_listener::{self.rule_id}")
            self.is_running = False
            self.logger(f"Stopped listening for '{self.event_name}'.", "INFO")


class EventBusTriggerModule(BaseModule, IExecutable, IDataPreviewer):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        event_name = config.get("event_name_to_listen", "UNKNOWN_EVENT")


        trigger_source = "manual_simulation"
        status_updater(f"Simulating Trigger for event: {event_name}", "INFO")

        if 'data' not in payload:
            payload['data'] = {}

        payload['data']['trigger_info'] = {
            'type': 'event_bus',
            'event_name': event_name,
            'source': trigger_source,
            'timestamp': datetime.datetime.now().isoformat(),
            'event_data': {
                'message': 'This is a simulated event payload.',
                'mock_id': str(uuid.uuid4())[:8]
            }
        }

        self.logger(f"Event Trigger manually fired for '{event_name}'", "INFO")
        status_updater("Workflow triggered manually.", "SUCCESS")

        return {"payload": payload, "output_name": "output"}

    def get_data_preview(self, config: dict):
        event = config.get("event_name_to_listen", "Not Configured")
        return [{
            "status": "listening",
            "message": f"Event: {event}",
            "details": {"topic": event}
        }]
