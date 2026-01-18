########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\gateway_connector_service\log_handler.py total lines 55 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging
import asyncio

class SocketIOLogHandler(logging.Handler):
    """
    Custom Log Handler that intercepts logs from Core and emits them
    to the Gateway via SocketIO ('engine_log' event).
    """
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record):
        if record.name.startswith(('socketio', 'engineio', 'aiohttp', 'urllib3', 'requests', 'werkzeug')):
            return

        if not getattr(self.service, 'is_authenticated', False) or not getattr(self.service.sio, 'connected', False):
            return

        try:
            msg = self.format(record)

            log_target_user = getattr(record, 'user_id', None)
            if not log_target_user:
                 log_target_user = getattr(self.service, 'user_id', None)

            payload = {
                'timestamp': record.created,
                'level': record.levelname,
                'message': msg,
                'source': 'core',
                'engine_id': getattr(self.service, 'engine_id', 'unknown'),
                'user_id': log_target_user,
                'metadata': {
                    'logger': record.name,
                    'func': record.funcName,
                    'lineno': record.lineno
                }
            }

            main_loop = getattr(self.service, '_main_loop', None)
            if main_loop and main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.service.emit_to_gateway('engine_log', payload),
                    main_loop
                )
        except Exception:
            self.handleError(record)
