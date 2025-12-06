########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\triggers\file_system_trigger\listener.py total lines 95 
########################################################################

import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flowork_kernel.api_contract import BaseTriggerListener

class _InternalEventHandler(FileSystemEventHandler):
    """Internal handler bridging Watchdog events to Flowork Listener."""
    def __init__(self, listener_instance, events_to_watch):
        self.listener = listener_instance
        self.events_to_watch = events_to_watch

    def _process(self, event, event_type):
        if event.is_directory:
            return

        if event_type not in self.events_to_watch:
            return

        trigger_payload = {
            "trigger_info": {
                "type": "file_system",
                "event_type": event_type,
                "src_path": event.src_path,
                "is_directory": False,
                "filename": os.path.basename(event.src_path),
                "timestamp": time.time()
            },
            "data": {
                "file_path": event.src_path,
                "filename": os.path.basename(event.src_path)
            }
        }

        if event_type == 'moved':
            trigger_payload["trigger_info"]["dest_path"] = event.dest_path
            trigger_payload["data"]["file_path"] = event.dest_path # Update to new location

        self.listener.logger(f"File Event Detected: {event_type} -> {event.src_path}", "INFO")
        self.listener._on_event(trigger_payload)

    def on_created(self, event):
        self._process(event, "created")

    def on_modified(self, event):
        self._process(event, "modified")

    def on_deleted(self, event):
        self._process(event, "deleted")

    def on_moved(self, event):
        self._process(event, "moved")


class FileSystemListener(BaseTriggerListener):

    def __init__(self, trigger_id, config, services, **kwargs):
        super().__init__(trigger_id, config, services, **kwargs)
        self.path_to_watch = self.config.get("path_to_watch")
        raw_events = self.config.get("events_to_watch", ["created"])
        self.events_to_watch = raw_events if isinstance(raw_events, list) else [raw_events]
        self.recursive = self.config.get("recursive", False)
        self.observer = None

    def start(self):
        if not self.path_to_watch or not os.path.isdir(self.path_to_watch):
            self.logger(f"FS Trigger '{self.rule_id}' failed: Path '{self.path_to_watch}' invalid.", "ERROR")
            return

        event_handler = _InternalEventHandler(self, self.events_to_watch)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.path_to_watch, recursive=self.recursive)

        try:
            self.observer.start()
            self.is_running = True
            self.logger(f"FS Trigger started on '{self.path_to_watch}' [{', '.join(self.events_to_watch)}]", "INFO")
        except Exception as e:
            self.logger(f"Failed to start Watchdog: {e}", "ERROR")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        self.is_running = False
        self.logger(f"FS Trigger stopped.", "INFO")
