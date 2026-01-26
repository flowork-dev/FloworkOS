########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\get_assigned_port.py total lines 37 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import socket

def is_port_in_use(port: int) -> bool:
    """Cek apakah port sedang digunakan oleh proses lain di OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run(hub, app_id: str) -> int:
    """
    Assign or retrieve existing port for an App.
    Fix: Menjamin port unik lintas App meski proses belum sepenuhnya bind (Fase 3).
    """
    if app_id in hub.port_registry:
        return hub.port_registry[app_id]

    reserved_ports = set(hub.port_registry.values())

    candidate = hub.next_port

    while candidate in reserved_ports or is_port_in_use(candidate):
        hub.logger.debug(f"⚠️ Port {candidate} is unavailable (Reserved/Busy), trying next...")
        candidate += 1
        if candidate > 65000: # Batas aman port TCP
            candidate = 5001

    hub.port_registry[app_id] = candidate

    hub.next_port = candidate + 1

    hub.logger.info(f"🔌 [PortManager] Assigned unique port {candidate} to {app_id}")
    return candidate
