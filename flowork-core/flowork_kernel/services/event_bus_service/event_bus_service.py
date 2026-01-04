########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\event_bus_service.py total lines 207 
########################################################################

"""
document : https://flowork.cloud/p-tinjauan-arsitektur-event_bus_servicepy-jaringan-saraf-pusat-flowork-id.html
Description:
    Service ini bertindak sebagai "Sistem Saraf" Flowork.
    Menggunakan Arsitektur "Immortality Matrix" untuk penanganan error bertingkat.
    [PHASE 5] Sekarang mendukung App-to-App Event Propagation.
"""

import asyncio
import logging
import multiprocessing
import queue
import threading
import time
import traceback
from flowork_kernel.services.base_service import BaseService


class EventBusService(BaseService):

    def __init__(self, kernel, service_id, ipc_queue: multiprocessing.Queue = None):
        super().__init__(kernel, service_id)
        self.subscribers = {} # Internal Service Subscribers
        self.app_subscriptions = {} # [PHASE 5] External App Subscribers { "event_name": [("app_id", "action_name")] }

        self.ipc_queue = ipc_queue

        self.is_main_bus = False
        self._main_loop = None
        self._ipc_thread = None
        self._stop_event = threading.Event()

        self.pub_max_retries = 3
        self.pub_backoff = 0.1 # detik
        self.ipc_thread_health = True # Indikator kesehatan thread listener

        if self.ipc_queue:
            self.logger.info(f"✅ EventBus initialized with IPC Queue (Neural Link Active).")
        else:
            self.logger.warning(f"⚠️ EventBus initialized WITHOUT IPC Queue. Cross-process bridging will FAIL.")

    def set_main_loop(self, loop):
        """Mengaktifkan mode Main Bus dan menyalakan 'Telinga' (IPC Listener)"""
        self.is_main_bus = True
        self._main_loop = loop
        self.logger.info("[MainBus] EventBus set to Main mode. Igniting Neural Listener...")

        if self.ipc_queue:
            self._start_ipc_listener()

    def _start_ipc_listener(self):
        """Helper untuk spawn thread listener baru (Re-generation capability)"""
        if self._ipc_thread and self._ipc_thread.is_alive():
            return # Sudah hidup, jangan spawn double

        self._stop_event.clear()
        self._ipc_thread = threading.Thread(target=self._run_ipc_listener_thread, daemon=True, name="IPC_Listener_Thread")
        self._ipc_thread.start()
        self.logger.info("👂 IPC Listener Thread spawned.")

    def subscribe(self, event_pattern: str, subscriber_id: str, callback: callable):
        """Mendaftarkan 'Organ Tubuh' (Internal Service) ke sistem saraf"""
        if subscriber_id in self.subscribers:
             self.logger.warning(f"Subscriber ID '{subscriber_id}' overwriting subscription for '{event_pattern}'.")

        self.logger.info(f"[Neural] SUBSCRIBE: '{subscriber_id}' linked to synapse '{event_pattern}'.")
        self.subscribers[subscriber_id] = (event_pattern, callback)

    def subscribe_app(self, event_pattern: str, app_id: str, action_name: str):
        """
        Mendaftarkan App Eksternal agar dibangunkan saat event terjadi.
        """
        if event_pattern not in self.app_subscriptions:
            self.app_subscriptions[event_pattern] = []

        entry = (app_id, action_name)
        if entry not in self.app_subscriptions[event_pattern]:
            self.app_subscriptions[event_pattern].append(entry)
            self.logger.info(f"🔌 [Nervous] App '{app_id}' attached to event '{event_pattern}' (Action: {action_name})")

    def unsubscribe(self, subscriber_id: str):
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            self.logger.debug(f"Unsubscribed: {subscriber_id}")
        else:
             self.logger.warning(f"Attempted to unsubscribe ghost ID: {subscriber_id}")

    def publish(self, event_name: str, payload: dict, publisher_id: str = "SYSTEM"):
        """
        Mengirim sinyal saraf ke seluruh tubuh (Internal & Eksternal).
        """
        if event_name not in ["WORKFLOW_EXECUTION_UPDATE", "NODE_STATUS_UPDATE"]:
             self.logger.debug(f"[Event] '{event_name}' from '{publisher_id}'")

        if payload and event_name == "WORKFLOW_LOG_ENTRY":
             self.logger.info(f"[LOG STREAM] {payload.get('message', '')}")

        if not self.is_main_bus and self.ipc_queue:
            sent = False
            attempts = 0
            while not sent and attempts < self.pub_max_retries:
                try:
                    self.ipc_queue.put_nowait((event_name, payload, publisher_id))
                    sent = True
                except queue.Full:
                    attempts += 1
                    if attempts < self.pub_max_retries:
                        time.sleep(self.pub_backoff * attempts)
                    else:
                        self.logger.error(f"[{publisher_id}] 🔴 TIER 1 FAIL: IPC Queue FULL. Dropping event '{event_name}'.")
                except Exception as e:
                    self.logger.error(f"[{publisher_id}] Error forwarding IPC: {e}")
                    attempts += 1

        current_subscribers = list(self.subscribers.items())
        for subscriber_id, (pattern, callback) in current_subscribers:
            if pattern == '*' or pattern == event_name:
                self._dispatch_event(event_name, subscriber_id, callback, payload)

        app_targets = self.app_subscriptions.get(event_name, [])

        if app_targets:
            app_runtime = self.kernel.get_service("app_runtime")
            if app_runtime:
                for app_id, action_name in app_targets:
                    self.logger.info(f"⚡ [Nervous] Triggering App {app_id}:{action_name} for event {event_name}")
                    app_runtime.trigger_event_handler(app_id, action_name, payload)

    def _dispatch_event(self, event_name, subscriber_id, callback, payload):
        """
        Firewall Callback: Memastikan error di satu App tidak membunuh EventBus.
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                if self._main_loop and self._main_loop.is_running():
                    asyncio.run_coroutine_threadsafe(callback(event_name, subscriber_id, payload), self._main_loop)
                else:
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(callback(event_name, subscriber_id, payload))
                    except RuntimeError:
                        asyncio.run(callback(event_name, subscriber_id, payload))
            else:
                callback(event_name, subscriber_id, payload)

        except Exception as e:
            self.logger.error(f"⚠️ DISPATCH ERROR for '{subscriber_id}': {e}")

    def _run_ipc_listener_thread(self):
        """
        [MATA-MATA ABADI] Thread khusus untuk mendengar pesan dari Worker.
        Dilengkapi dengan TIER 2 & 3 Error Handling.
        """
        self.logger.info("[MainBus] IPC Thread Listener started. Polling queue...")
        self.ipc_thread_health = True

        while not self._stop_event.is_set():
            try:
                event_data = self.ipc_queue.get(timeout=1.0)

                if event_data:
                    event_name, payload, publisher_id = event_data

                    self.publish(event_name, payload, publisher_id=publisher_id or "IPC_BRIDGE")

            except queue.Empty:
                continue # Normal, antrian kosong

            except (EOFError, BrokenPipeError) as e:
                self.logger.critical(f"🔥 BROKEN PIPE DETECTED! IPC Link Severed: {e}")
                self.ipc_thread_health = False

                if hasattr(self, 'handle_injury'):
                    self.handle_injury(e)

                break # Keluar loop, thread mati (nanti di-revive sama run_logic kalo Tier 2)

            except Exception as e:
                self.logger.error(f"[MainBus] Error in IPC Thread: {e}")
                time.sleep(1) # Backoff sebentar

        self.logger.info("[MainBus] IPC Thread Listener STOPPED.")

    async def load_dependencies(self):
        self.logger.info("EventBusService dependencies loaded.")

    def run_logic(self):
        """
        Loop utama Service.
        Bertugas memonitor kesehatan komponen internal (seperti IPC Thread).
        """
        while self.is_running:
            if self.is_main_bus and self.ipc_queue:
                if self._ipc_thread is None or not self._ipc_thread.is_alive():
                    if self.ipc_thread_health: # Jika sebelumnya sehat, berarti mati mendadak
                        self.logger.warning("♻️ [Tier 2 Recovery] IPC Thread found DEAD. Respawning...")
                        self._start_ipc_listener()
                    else:
                         pass

            time.sleep(2)
