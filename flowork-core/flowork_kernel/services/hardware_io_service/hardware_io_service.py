########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\hardware_io_service\hardware_io_service.py total lines 57 
########################################################################

import os
import sys
import logging
from flowork_kernel.services.base_service import BaseService

class HardwareIOService(BaseService):
    """
    [THE INDRA] Hardware Interface Service.
    Handles Camera, Microphone, and GPIO for IoT/Robotics.
    Status: ACTIVE SCANNING
    """
    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)
        self.available_sensors = []
        self.audio_devices = [] # --- ADDED: Per Rule 1 ---
        self.is_hardware_isolated = True

    def start(self):
        """Memulai pemindaian indra sistem"""
        self.logger.info("👁️ HardwareIOService (Indra) is ONLINE.")
        self._scan_hardware_capabilities()

    def _scan_hardware_capabilities(self):
        """Mengecek akses ke hardware fisik (Kamera & Audio)"""
        self.logger.info("🔍 Indra scanning for physical interfaces...")

        if os.path.exists("/dev/video0"):
            self.available_sensors.append("camera_0")
            self.logger.info("📸 Camera detected at /dev/video0")

        if os.path.exists("/proc/asound/cards"):
            try:
                with open("/proc/asound/cards", "r") as f:
                    cards = f.read()
                    self.audio_devices.append("system_audio")
                    self.logger.info(f"🔊 Audio Hardware Detected:\n{cards}")
            except Exception as e:
                self.logger.error(f"🚫 Failed to read audio cards: {e}")
        else:
            self.logger.info("🔇 No physical audio hardware detected in this sector.")

    def capture_audio_sample(self, duration=3):
        """Simulasi penangkapan sinyal audio (Testing Only)"""
        if not self.audio_devices:
            return {"status": "error", "message": "No audio hardware linked."}

        self.logger.info(f"👂 Indra is listening for {duration}s...")
        return {"status": "success", "data": "AUDIO_SIGNAL_CAPTURED"}

    def stop(self):
        self.logger.info("👁️ Indra closing eyes. HardwareIO stopped.")
