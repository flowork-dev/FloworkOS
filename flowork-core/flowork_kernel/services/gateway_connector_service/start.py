########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\start.py total lines 170 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import socketio
import os
import asyncio
import logging
import multiprocessing
import json
from flowork_kernel.singleton import Singleton
from .log_handler import SocketIOLogHandler

async def run(hub):
    """
    [OVERRIDDEN] Async Entry Point.
    Mengimplementasikan IMMORTALITY MATRIX untuk koneksi SocketIO.
    """

    try:
        hub._main_loop = asyncio.get_running_loop()
        hub.logger.info(f'[MATA-MATA] Main Async Loop Captured: {hub._main_loop}')
    except:
        hub.logger.error('[MATA-MATA] FAILED TO CAPTURE MAIN LOOP IN START!')

    try:
        job_evt = multiprocessing.Event()
        Singleton.set_instance(multiprocessing.Event, job_evt)
        Singleton.set_instance('job_event', job_evt)
        hub.logger.info('✅ [MATA-MATA] Job Event (Bell) registered to Singleton.')
    except Exception as e:
        hub.logger.error(f'❌ [MATA-MATA] Failed to register Job Event: {e}')

    try:
        eb = hub.kernel_services.get('event_bus') or Singleton.get_instance('event_bus')
        if eb and hasattr(eb, 'set_main_loop'):
            eb.set_main_loop(hub._main_loop)
            hub.logger.info('✅ [MATA-MATA] EventBus Main Loop Activated! IPC Bridge is OPEN.')
        else:
            hub.logger.warning('⚠️ [MATA-MATA] EventBus not found or incompatible during start.')
    except Exception as e:
        hub.logger.error(f'❌ [MATA-MATA] Failed to activate EventBus loop: {e}')

    try:
        root_logger = logging.getLogger()
        has_handler = any(isinstance(h, SocketIOLogHandler) for h in root_logger.handlers)
        if not has_handler:
            log_courier = SocketIOLogHandler(hub)
            root_logger.addHandler(log_courier)
            hub.logger.info('✅ [MATA-MATA] Log Courier attached. Core logs will be streamed to GUI.')
    except Exception as e:
        hub.logger.error(f'❌ [MATA-MATA] Failed to attach Log Courier: {e}')

    if not hub.engine_id or not hub.engine_token or (not hub.gateway_url):
        hub.logger.critical('MISSING ENV VARS for Gateway Connection!')
        return

    resolved_url = hub.execute_sync('_resolve_home_gateway')

    if 'gw-' in resolved_url and 'gateway' not in resolved_url:
        resolved_url = 'http://gateway:8000'

    connect_url = resolved_url.replace('http', 'ws')
    if 'gateway' in connect_url and ':' not in connect_url.split('//')[1]:
        connect_url = connect_url.rstrip('/') + ':8000'

    hub.gateway_url = connect_url
    auth_payload = {'engine_id': hub.engine_id, 'token': hub.engine_token}

    register_events(hub, auth_payload)

    hub.logger.info(f'📡 [MATA-MATA] Client connecting to: {connect_url}')

    while hub.is_running:
        try:
            await hub.sio.connect(
                connect_url,
                auth=auth_payload,
                namespaces=['/engine-socket'],
                socketio_path='/api/socket.io',
                transports=['websocket']
            )
            await hub.sio.wait()
        except Exception as e:
            hub.logger.error(f'Gateway Connection Error: {e}')
            hub.retry_count += 1
            if hub.retry_count > 5:
                hub.logger.critical('⚠️ Too many connection failures. Escalating...')
                await asyncio.sleep(10)
            else:
                await asyncio.sleep(5)
            hub.is_authenticated = False

def register_events(hub, auth_payload):
    """Mendaftarkan event handler SocketIO"""

    @hub.sio.on('connect', namespace='/engine-socket')
    async def on_connect():
        hub.logger.info(f'✅ [MATA-MATA] SOCKET PHYSICALLY CONNECTED')
        await hub.sio.emit('authenticate', auth_payload, namespace='/engine-socket')

        hub.execute_sync('set_kernel_services', hub.kernel_services)

        hub.retry_count = 0

    @hub.sio.on('auth_success', namespace='/engine-socket')
    async def on_auth_success(data):
        hub.user_id = data.get('user_id')
        hub.is_authenticated = True
        hub.logger.info(f'🛡️ [MATA-MATA] AUTH SUCCESS. User: {hub.user_id}')

        asyncio.create_task(hub.execute_async('_send_engine_ready'))

        if not hub._hb_task:
            hub._hb_task = asyncio.create_task(hub.execute_async('_engine_heartbeat'))
        if not hub._watchdog_task:
            hub._watchdog_task = asyncio.create_task(hub.execute_async('_run_watchdog'))

    @hub.sio.on('disconnect', namespace='/engine-socket')
    async def on_disconnect():
        hub.is_authenticated = False
        hub.logger.warning('🔌 Socket Disconnected.')

    @hub.sio.on('gw:dispatch_event', namespace='/engine-socket')
    async def on_gateway_event(data):
        try:
            if not isinstance(data, dict): return
            payload = data.get('payload', data)
            event_name = payload.get('event_name')
            event_data = payload.get('event_data', {})
            source = payload.get('source', 'gateway')

            if event_name:
                hub.logger.info(f'⚡ [Nervous System] Received inbound event: {event_name}')
                eb = hub.kernel_services.get('event_bus') or Singleton.get_instance('event_bus')
                if eb:
                    eb.publish(event_name, event_data, source_app_id=f'gateway_{source}')
        except Exception as e:
            hub.logger.error(f'❌ [Nervous System] Dispatch Error: {e}')

    @hub.sio.on('db_proxy', namespace='/engine-socket')
    async def on_db_proxy(data):
        try:
            db_service = hub.kernel_services.get('database_service')
            if not db_service:
                return {'status': 'error', 'error': 'Database Service Unavailable'}

            action = data.get('action')
            collection = data.get('collection')
            payload = data.get('payload', {})
            app_id = data.get('app_id')

            if not app_id: return {'status': 'error', 'error': 'Missing App ID'}

            result = None
            if action == 'insert':
                result = await db_service.insert_app_data(app_id, collection, payload.get('value'))
            elif action in ['select', 'find']:
                result = await db_service.get_app_data(app_id, collection, payload.get('key'))
            elif action == 'delete':
                result = await db_service.delete_app_data(app_id, collection, payload.get('key'))
            else:
                return {'status': 'error', 'error': f'Unknown DB action: {action}'}

            return {'status': 'success', 'data': result}
        except Exception as e:
            hub.logger.error(f'❌ [Iron Bank] Transaction Failed: {e}')
            return {'status': 'error', 'error': str(e)}
