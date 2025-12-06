########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\workers\watchdog.py total lines 175 
########################################################################

import threading
import time
import logging
import os
import sys
import subprocess
import hashlib
from typing import Callable

class JobWatchdog:
    def __init__(self, deadline_seconds: int = 60, on_timeout: Callable[[str], None] = None):
        self.deadline = deadline_seconds
        self.on_timeout = on_timeout or (lambda job_id: None)

    def run_with_deadline(self, job_id: str, fn: Callable, *args, **kwargs):
        result_container = {"value": None, "error": None}

        t = threading.Thread(target=self._runner, args=(result_container, fn, args, kwargs), daemon=True)
        start = time.time()
        t.start()

        t.join(timeout=self.deadline)

        duration = time.time() - start

        if t.is_alive():
            print(f"!!! [WATCHDOG] CRITICAL: JOB TIMEOUT! Job {job_id} is stuck.", flush=True)
            self.on_timeout(job_id)
            result_container["error"] = TimeoutError(f"Job {job_id} exceeded {self.deadline}s")

        return result_container["value"], result_container["error"]

    def _runner(self, box, fn, args, kwargs):
        try:
            box["value"] = fn(*args, **kwargs)
        except Exception as e:
            print(f"!!! [WATCHDOG] Thread Exception: {e}", flush=True)
            box["error"] = e

class DependencyWatchdog:
    def __init__(self, kernel):
        self.kernel = kernel
        self.logger = self._wrap_logger(getattr(kernel, 'write_to_log', None) or getattr(kernel, 'logger', None))

        self.active = True
        self._install_lock = threading.Lock()

        self.target_dirs = [
            'modules', 'plugins', 'tools', 'triggers',
            'widgets', 'scanners', 'ai_providers'
        ]

    def _wrap_logger(self, logger_instance):
        """Adapter agar logger bisa dipanggil dengan .info() atau ("msg", "INFO")"""
        class LoggerAdapter:
            def __init__(self, l): self.l = l
            def info(self, msg): self._log(msg, "INFO")
            def error(self, msg): self._log(msg, "ERROR")
            def warning(self, msg): self._log(msg, "WARN")
            def _log(self, msg, level):
                if not self.l: print(f"[{level}] {msg}")
                elif callable(self.l): self.l(msg, level)
                elif hasattr(self.l, level.lower()): getattr(self.l, level.lower())(msg)
        return LoggerAdapter(logger_instance)

    def start(self):
        """Jalankan Watchdog di Thread terpisah"""
        self.logger.info("🐶 [Watchdog] Dependency Guardian STARTED.")
        thread = threading.Thread(target=self._loop, daemon=True, name="Flowork-DepWatchdog")
        thread.start()

    def _loop(self):
        time.sleep(3)

        self.logger.info("🚀 [Watchdog] INITIAL BOOT SCAN: Hunting for missing dependencies...")
        self.scan_and_install(verbose=True) # Scan pertama yang cerewet
        self.logger.info("✅ [Watchdog] INITIAL SCAN COMPLETE.")

        while self.active:
            try:
                time.sleep(10) # Cek setiap 10 detik
                self.scan_and_install(verbose=False)
            except Exception as e:
                self.logger.error(f"🐶 [Watchdog] Loop Error: {e}")

    def _get_root_path(self):
        """Deteksi lokasi root (Docker /app atau Local)"""
        if os.path.exists("/app/modules"): return "/app"

        cwd = os.getcwd()
        try:
            kernel_path = getattr(self.kernel, "project_root_path", None)
            if kernel_path and os.path.exists(os.path.join(kernel_path, "modules")):
                return kernel_path
        except: pass

        return cwd

    def scan_and_install(self, verbose=False):
        root_path = self._get_root_path()
        if verbose: self.logger.info(f"🔍 [Watchdog] Scanning Root: {root_path}")

        for category in self.target_dirs:
            base_path = os.path.join(root_path, category)
            if not os.path.exists(base_path): continue

            try: items = os.listdir(base_path)
            except: continue

            for item_name in items:
                item_path = os.path.join(base_path, item_name)

                if not os.path.isdir(item_path) or item_name.startswith('.'): continue

                is_target = "golden_moment" in item_name
                if is_target and verbose:
                    self.logger.info(f"🧐 [Watchdog] Checking Target: {item_name}")

                if self._needs_install(item_path, verbose=(verbose and is_target)):
                    with self._install_lock:
                        if self._needs_install(item_path):
                            label = f"[{category.upper()}] {item_name}"
                            self.logger.info(f"📦 [Watchdog] Auto-Installing: {label}")
                            self._install_pip(item_path, label)

    def _needs_install(self, path, verbose=False):
        req_file = os.path.join(path, "requirements.txt")
        if not os.path.exists(req_file):
            if verbose: self.logger.info("   -> requirements.txt MISSING")
            return False

        installed_marker = os.path.join(path, ".installed")
        if not os.path.exists(installed_marker):
            if verbose: self.logger.info("   -> .installed marker MISSING (New Component)")
            return True

        try:
            if os.path.getmtime(req_file) > os.path.getmtime(installed_marker):
                if verbose: self.logger.info("   -> Requirements UPDATED (Re-installing)")
                return True
        except: return True

        if verbose: self.logger.info("   -> Up-to-date")
        return False

    def _install_pip(self, path, label):
        req_file = os.path.join(path, "requirements.txt")
        marker = os.path.join(path, ".installed")

        cmd = [
            sys.executable, "-m", "pip", "install",
            "-r", req_file,
            "--disable-pip-version-check",
            "--prefer-binary"
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            if res.returncode == 0:
                with open(marker, "w") as f: f.write(f"Installed on {time.ctime()}")
                self.logger.info(f"✅ [Watchdog] Success: {label}")
                return True
            else:
                self.logger.error(f"❌ [Watchdog] FAILED: {label}\nLOG: {res.stdout[:500]}...")
                return False
        except Exception as e:
            self.logger.error(f"❌ [Watchdog] Error executing pip: {e}")
            return False
