########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\start_flowork.py total lines 169 
########################################################################

import os
import sys
import subprocess
import time
import signal
import platform
import threading

ENV_FILE = ".env"
GATEWAY_SCRIPT = os.path.join("flowork-gateway", "run_gateway.py") # Pastikan path ini sesuai
CLOUDFLARED_PATH_WIN = os.path.join("cloudflared", "cloudflared.exe")
CLOUDFLARED_PATH_UNIX = "cloudflared" # Assumes it's in PATH for Linux/Mac

processes = []

def read_env_value(key):
    """
    (English Hardcode) Reads a specific key from .env file manually
    to avoid external dependencies like python-dotenv in this launcher.
    """
    if not os.path.exists(ENV_FILE):
        return None

    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    except Exception as e:
        print(f"[Launcher Error] Failed to read .env: {e}")
    return None

def stream_logs(process, prefix):
    """
    (English Hardcode) Reads output from a subprocess and prints it with a prefix.
    """
    for line in iter(process.stdout.readline, b''):
        try:
            line_str = line.decode('utf-8').strip()
            if line_str:
                print(f"[{prefix}] {line_str}")
        except:
            pass

def cleanup_processes(signum=None, frame=None):
    """
    (English Hardcode) Kills all started processes on exit.
    """
    print("\n[Launcher] Stopping all services...")
    for p in processes:
        try:
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass
    print("[Launcher] Shutdown complete. Bye!")
    sys.exit(0)

def main():
    print("###################################################")
    print("#           FLOWORK ENGINE LAUNCHER               #")
    print("#       (Zero Cost - Zero Risk Architecture)      #")
    print("###################################################")

    tunnel_token = read_env_value("TUNNEL_TOKEN")
    socket_url = read_env_value("SOCKET_URL")

    if not tunnel_token or "PASTE_" in tunnel_token:
        print("\n[ERROR] TUNNEL_TOKEN is missing or invalid in .env")
        print("Please edit .env and paste your Cloudflare Tunnel Token.")
        input("Press Enter to exit...")
        sys.exit(1)

    if not socket_url:
        print("\n[WARNING] SOCKET_URL is not set in .env.")
        print("CORS might block requests from the GUI.")

    print(f"\n[Launcher] Starting Tunnel connection to {socket_url or 'Cloudflare Edge'}...")

    cf_cmd = []
    if platform.system() == "Windows":
        if os.path.exists(CLOUDFLARED_PATH_WIN):
            cf_cmd = [CLOUDFLARED_PATH_WIN, "tunnel", "run", "--token", tunnel_token]
        else:
            print(f"[ERROR] cloudflared.exe not found at {CLOUDFLARED_PATH_WIN}")
            print("Make sure you have downloaded cloudflared.exe into the 'cloudflared' folder.")
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        cf_cmd = ["cloudflared", "tunnel", "run", "--token", tunnel_token]

    try:
        cf_process = subprocess.Popen(
            cf_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr to stdout
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0,
            preexec_fn=os.setsid if platform.system() != "Windows" else None
        )
        processes.append(cf_process)

        t = threading.Thread(target=stream_logs, args=(cf_process, "TUNNEL"))
        t.daemon = True
        t.start()

        print("[Launcher] Tunnel service started.")

    except Exception as e:
        print(f"[ERROR] Failed to start cloudflared: {e}")
        sys.exit(1)

    print("[Launcher] Starting Flowork Gateway/Engine...")

    if not os.path.exists(GATEWAY_SCRIPT):
         print(f"[ERROR] Gateway script not found at {GATEWAY_SCRIPT}")
         print("Please check your folder structure.")
         cleanup_processes()

    gw_cmd = [sys.executable, GATEWAY_SCRIPT]

    try:
        gw_process = subprocess.Popen(
            gw_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0,
            preexec_fn=os.setsid if platform.system() != "Windows" else None
        )
        processes.append(gw_process)

        t2 = threading.Thread(target=stream_logs, args=(gw_process, "GATEWAY"))
        t2.daemon = True
        t2.start()

    except Exception as e:
        print(f"[ERROR] Failed to start Gateway: {e}")
        cleanup_processes()

    print("\n[SUCCESS] Flowork is running!")
    print(f"[INFO] Engine URL: {socket_url}")
    print("[INFO] Press Ctrl+C to stop everything.\n")

    try:
        while True:
            if cf_process.poll() is not None:
                print("\n[CRITICAL] Cloudflare Tunnel died unexpectedly!")
                break
            if gw_process.poll() is not None:
                print("\n[CRITICAL] Flowork Gateway died unexpectedly!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_processes()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup_processes)
    signal.signal(signal.SIGTERM, cleanup_processes)
    main()
