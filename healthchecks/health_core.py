########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\healthchecks\health_core.py total lines 33 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import sys
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
PORTS = [8990, 8989, 5001]
PATHS = ["/health", "/status", "/metrics", "/"]
def healthy() -> bool:
    for p in PORTS:
        for path in PATHS:
            url = f"http://127.0.0.1:{p}{path}"
            try:
                with urlopen(url, timeout=2) as r:
                    if 200 <= r.status < 500:
                        print(f"[OK] Core alive at {url} status={r.status}")
                        return True
            except HTTPError as e:
                if 400 <= e.code < 500:
                    print(f"[OK] Core alive (HTTP {e.code}) at {url}")
                    return True
                print(f"[WARN] HTTP {e.code} at {url}")
            except URLError as e:
                print(f"[WAIT] {url} unreachable: {e.reason}")
            except Exception as e:
                print(f"[ERR] {url} error: {e}")
    return False
if healthy():
    sys.exit(0)
sys.exit(1)
