########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_service.py total lines 202 
########################################################################

import logging
import os
import shutil
import time
import traceback
import threading
from enum import Enum
from pathlib import Path

class RecoveryTier(Enum):
    TIER_1_SELF_HEAL = 1   # Luka Lecet: Retry + Backoff
    TIER_2_SOFT_RESTART = 2 # Pingsan: Reset Loop/Thread
    TIER_3_HARD_RESTART = 3 # Mati Suri: Minta VitalityService Kill Process
    TIER_4_KERNEL_PANIC = 4 # Kiamat: Reboot System

class BaseService:
    def __init__(self, kernel, service_id: str, vitality_doctor=None):
        self.kernel = kernel
        self.service_id = service_id
        self.doctor = vitality_doctor  # Referensi ke VitalityService (Dokter)
        self.logger = logging.getLogger(f"Node.{service_id}")

        self._loc_cache = None
        self.is_running = False
        self.retry_count = 0
        self.max_retries = 3

    @property
    def loc(self):
        if self._loc_cache is None:
            self._loc_cache = self.kernel.get_service('localization_manager')
        return self._loc_cache


    def _resolve_and_secure_path(self, relative_path, user_id):
        """
        [Node-Path Logic]
        Resolves physical paths for workflow execution.
        Strictly prevents escaping user jail during logic operations.
        """
        from flowork_kernel.utils.path_helper import get_data_directory

        data_dir = get_data_directory()
        user_jail = Path(os.path.abspath(data_dir / "users" / str(user_id)))
        if not user_jail.exists(): user_jail.mkdir(parents=True, exist_ok=True)

        path_str = str(relative_path or "").strip()

        if path_str in ["", ".", "/", "\\", "ROOT", "default"]:
            return user_jail, user_jail

        virtual_prefix = "/app/data"
        target_path = None
        normalized_str = path_str.replace("\\", "/")

        if normalized_str.startswith(virtual_prefix):
            relative_part = normalized_str[len(virtual_prefix):].lstrip("/")
            possible_target = Path(os.path.abspath(data_dir / relative_part))
            if str(possible_target).startswith(str(user_jail)):
                target_path = possible_target

        if not target_path:
            try:
                possible_abs = Path(os.path.abspath(path_str))
                if str(possible_abs).startswith(str(user_jail)):
                    target_path = possible_abs
            except: pass

        if not target_path:
            clean_rel = path_str.lstrip("/\\")
            target_path = Path(os.path.abspath(user_jail / clean_rel))

        if not str(target_path).startswith(str(user_jail)):
            self.logger.warning(f"🚨 [Security] Node Path Escape Attempt by {user_id}. Target: {target_path}")
            raise PermissionError("Security: Path Escape Attempt Detected")

        return target_path, user_jail

    def secure_list_directory(self, path, user_id):
        """[Logical Path] List directory without UI-specific '..' breadcrumbs."""
        try:
            target, _ = self._resolve_and_secure_path(path, user_id)
            items = []
            if target.exists() and target.is_dir():
                for item in sorted(os.listdir(target)):
                    if item.startswith('.'): continue
                    full_path = target / item
                    items.append({
                        "name": item,
                        "type": "directory" if full_path.is_dir() else "file",
                        "physical_path": str(full_path),
                        "path": str(full_path)
                    })
            return {"status": "success", "items": items, "current_path": str(target)}
        except Exception as e: return {"status": "error", "error": str(e)}

    def secure_create_folder(self, current_path, name, user_id):
        try:
            target, _ = self._resolve_and_secure_path(current_path, user_id)
            new_folder = target / name
            new_folder.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "physical_path": str(new_folder), "path": str(new_folder)}
        except Exception as e: return {"status": "error", "error": str(e)}

    def secure_delete_path(self, target_path_str, user_id):
        try:
            target, _ = self._resolve_and_secure_path(target_path_str, user_id)
            if not target.exists(): return {"status": "error", "error": "Not found"}
            if target.is_file(): os.remove(target)
            else: shutil.rmtree(target)
            return {"status": "success"}
        except Exception as e: return {"status": "error", "error": str(e)}


    def run_logic(self):
        """
        [Override Required]
        Logika utama service berjalan di sini.
        Anak (subclass) wajib mengisi ini jika butuh background process.
        """
        pass

    def start(self):
        """Jantung Utama: Menjalankan run_logic dalam perlindungan Try/Catch Abadi."""
        self.is_running = True
        self.logger.info(f"🚀 {self.service_id} STARTED with Immortal Matrix.")

        if self.__class__.run_logic == BaseService.run_logic:
            return

        threading.Thread(target=self._immortal_loop, daemon=True, name=f"{self.service_id}_Loop").start()

    def _immortal_loop(self):
        while self.is_running:
            try:
                self.run_logic()
                self.retry_count = 0
                break
            except Exception as e:
                self.handle_injury(e)

    def handle_injury(self, error):
        """
        🏥 RUANG UGD (Triage): Menentukan tingkat keparahan luka service.
        """
        self.retry_count += 1
        error_msg = str(error)
        stack_trace = traceback.format_exc()

        self.logger.error(f"⚠️ {self.service_id} INJURED (Strike {self.retry_count}): {error_msg}")

        tier = RecoveryTier.TIER_1_SELF_HEAL # Default: Luka ringan

        if "MemoryError" in error_msg or "BrokenPipe" in error_msg:
            tier = RecoveryTier.TIER_3_HARD_RESTART
        elif "SystemExit" in error_msg:
            tier = RecoveryTier.TIER_4_KERNEL_PANIC

        if self.retry_count > self.max_retries:
            self.logger.warning(f"🔄 {self.service_id} Exhausted retries. Escalating to Tier 2.")
            tier = RecoveryTier.TIER_2_SOFT_RESTART

        if tier == RecoveryTier.TIER_1_SELF_HEAL:
            time.sleep(2) # Napas dulu
            self.logger.info(f"🩹 {self.service_id} Self-healing...")

        elif tier == RecoveryTier.TIER_2_SOFT_RESTART:
            self.cleanup_resources()
            time.sleep(5)
            self.retry_count = 0 # Reset kesempatan
            self.logger.info(f"🧘 {self.service_id} Soft Restart completed.")

        elif tier == RecoveryTier.TIER_3_HARD_RESTART:
            if self.doctor:
                self.logger.critical(f"🚑 {self.service_id} Requesting HARD RESTART from Vitality!")
                self.doctor.report_critical_failure(self.service_id, stack_trace)
                self.is_running = False # Matikan diri, biar Dokter yang hidupin lagi
            else:
                self.logger.critical(f"💀 {self.service_id} Died without a Doctor. Process terminating.")
                exit(1)

        elif tier == RecoveryTier.TIER_4_KERNEL_PANIC:
             self.logger.critical("🔥 KERNEL PANIC! SYSTEM MELTDOWN!")
             if self.doctor:
                 self.doctor.trigger_system_reboot()
             else:
                 exit(1)

    def stop(self):
        self.is_running = False
        self.cleanup_resources()
        self.logger.info(f"🛑 {self.service_id} STOPPED")

    def cleanup_resources(self):
        """Override ini di anak untuk bersih-bersih memory/socket saat restart"""
        pass
