########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\test_muscle_trigger.py total lines 68 
########################################################################

import time
import sys
import os
import threading

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from flowork_kernel.kernel import Kernel
except ImportError:
    print("❌ ERROR: Tidak bisa import Kernel. Pastikan script ini ada di dalam folder 'flowork-core'.")
    sys.exit(1)

print("\n" + "="*50)
print("🚀 MEMULAI TEST ENGINE (OTOT ROBOT)")
print("="*50)

project_root = os.path.dirname(current_dir)
k = Kernel(project_root)

print(f"⚙️  Booting Kernel di: {project_root}")

threading.Thread(target=k._log_queue_worker, daemon=True).start()

k._load_services_from_manifest()

runtime = k.get_service("app_runtime")

if not runtime:
    print("❌ BAHAYA: Service 'app_runtime' TIDAK DITEMUKAN!")
    print("   Cek services.json lu bos, udah didaftarin belum?")
    sys.exit(1)

print("✅ Service 'app_runtime' DITEMUKAN!")
runtime.is_running = True
threading.Thread(target=runtime.run_logic, daemon=True).start()

print("\n👉 MENGIRIM PERINTAH KE 'universal_downloader'...")

result = runtime.execute_app(
    app_id="universal_downloader",
    action="download",
    params={
        "url": "https://www.youtube.com/watch?v=Myux6VbyORY", # Contoh video pendek
        "format_mode": "best" # Coba mode best (video+audio)
    },
    user_id="Tester_Manual_01"
)

print(f"   Status Launch: {result}")

if result['status'] == 'success':
    print("\n⏳ APLIKASI SEDANG JALAN DI BACKGROUND...")
    print("   (Pantau log di bawah ini, harusnya muncul progress bar dari yt-dlp)")
    print("   Menunggu 15 detik...")
    time.sleep(15)
else:
    print(f"❌ GAGAL START APP! Error: {result.get('error')}")

print("\n🏁 TEST SELESAI. Matikan Kernel.")
runtime.stop()
