########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\heartbeat.py total lines 22 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import threading, time, requests, os, logging
log = logging.getLogger(__name__)
GW_URL = os.getenv("GATEWAY_API_URL", "http://gateway:8000")
ENGINE_ID = os.getenv("FLOWORK_ENGINE_ID", "engine-dev")
HB_INTERVAL = int(os.getenv("ENGINE_HB_INTERVAL", "15"))
def _beat():
    while True:
        try:
            requests.post(f"{GW_URL}/internal/engine/heartbeat", json={"engine_id": ENGINE_ID}, timeout=15)
        except Exception as e:
            log.warning("Heartbeat missed (non-fatal): %s", e)
        time.sleep(HB_INTERVAL)
def start_heartbeat():
    log.info(f"Starting heartbeat thread. Beating to {GW_URL} every {HB_INTERVAL}s for ENGINE_ID {ENGINE_ID}")
    t = threading.Thread(target=_beat, daemon=True)
    t.start()
