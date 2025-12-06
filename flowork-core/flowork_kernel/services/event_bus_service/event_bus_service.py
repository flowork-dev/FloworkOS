########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\event_bus_service\event_bus_service.py total lines 129 
########################################################################

"""
document : https://flowork.cloud/p-tinjauan-arsitektur-event_bus_servicepy-jaringan-saraf-pusat-flowork-id.html
"""

import asyncio
import logging
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton
import multiprocessing
import queue


class EventBusService(BaseService):


    def __init__(self, kernel, service_id, ipc_queue: multiprocessing.Queue = None):

        super().__init__(kernel, service_id)
        self.subscribers = {}
        self.ipc_queue = ipc_queue

        self.is_main_bus = False
        self._main_loop = None

        if self.ipc_queue:
            self.logger.info(f"EventBus initialized with IPC Queue.")
        else:
            self.logger.warning(f"EventBus initialized WITHOUT IPC Queue. Event bridging will fail.")

    def set_main_loop(self, loop):

        self.is_main_bus = True
        self._main_loop = loop
        self.logger.info("[MainBus] EventBus set to Main mode. IPC listener will be started.")
        if self.ipc_queue and self._main_loop:
            asyncio.run_coroutine_threadsafe(self._check_ipc_queue_loop(), self._main_loop)

    def subscribe(self, event_pattern: str, subscriber_id: str, callback: callable):

        if subscriber_id in self.subscribers:
            self.logger.warning(f"Subscriber ID '{subscriber_id}' already exists. Overwriting subscription for pattern '{event_pattern}'.")
        self.logger.info(f"[MockKernel] SUBSCRIBE: Component '{subscriber_id}' successfully subscribed to event '{event_pattern}'.")
        self.subscribers[subscriber_id] = (event_pattern, callback)

    def unsubscribe(self, subscriber_id: str):

        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            self.logger.debug(f"Unsubscribed: {subscriber_id}")
        else:
            self.logger.warning(f"Attempted to unsubscribe non-existent ID: {subscriber_id}")

    def publish(self, event_name: str, payload: dict, publisher_id: str = "SYSTEM"):

        self.logger.info(f"[MockKernel] EVENT PUBLISHED: Name='{event_name}', Publisher='{publisher_id}'")
        if payload:
            try:
                log_payload = str(payload)
                if len(log_payload) > 500:
                    log_payload = log_payload[:500] + "... (truncated)"
                self.logger.info(f"[MockKernel] EVENT DATA: {log_payload}")
            except Exception as e:
                self.logger.warning(f"[MockKernel] Could not serialize event payload for logging: {e}")


        if not self.is_main_bus and self.ipc_queue:
            try:
                self.ipc_queue.put_nowait((event_name, payload, publisher_id))
                self.logger.info(f"[{publisher_id}] Forwarded event '{event_name}' to MainBus via IPC.")
            except queue.Full:
                self.logger.error(f"[{publisher_id}] IPC Event Queue is FULL. Failed to forward event '{event_name}'.")
            except Exception as e:
                self.logger.error(f"[{publisher_id}] Error forwarding event '{event_name}' via IPC: {e}")

        for subscriber_id, (pattern, callback) in self.subscribers.items():
            if pattern == '*' or pattern == event_name:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        try:
                            asyncio.create_task(callback(event_name, subscriber_id, payload))
                        except RuntimeError:
                            asyncio.run(callback(event_name, subscriber_id, payload))
                    else:
                        callback(event_name, subscriber_id, payload)

                    self.logger.debug(f"Event '{event_name}' dispatched to subscriber '{subscriber_id}'")
                except Exception as e:
                    self.logger.error(f"Error dispatching event '{event_name}' to '{subscriber_id}': {e}", exc_info=True)

    async def load_dependencies(self):

        self.logger.info("EventBusService dependencies loaded (IPC loop started if MainBus).")

    async def _check_ipc_queue_loop(self):

        if not self.is_main_bus or not self._main_loop:
            self.logger.error("[MainBus] Cannot start IPC listener: Not main bus or loop not set.")
            return

        self.logger.info("[MainBus] IPC Queue Listener started. Waiting for events from workers...")

        while True:
            try:
                event_data = await self._main_loop.run_in_executor(
                    None,
                    self.ipc_queue.get
                )

                if event_data:
                    event_name, payload, publisher_id = event_data
                    self.logger.info(f"[MainBus] Received '{event_name}' from IPC (Publisher: {publisher_id}). Republishing locally...")

                    self.publish(event_name, payload, publisher_id=publisher_id or "IPC_BRIDGE")

            except (asyncio.CancelledError, GeneratorExit):
                self.logger.info("[MainBus] IPC queue listener task cancelled.")
                break
            except Exception as e:
                if "got EOF" in str(e) or "Bad file descriptor" in str(e):
                    self.logger.warning(f"[MainBus] IPC queue closed. Shutting down listener. {e}")
                    break
                self.logger.error(f"[MainBus] Critical error in IPC queue listener loop: {e}", exc_info=True)
                await asyncio.sleep(1)
