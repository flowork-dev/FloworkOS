########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\vitality_service\vitality_service.py total lines 97 
########################################################################

import time
import threading
import traceback
import asyncio
import json
from flowork_kernel.services.base_service import BaseService
from flowork_kernel.singleton import Singleton

class VitalityService(BaseService):
    """[THE DOCTOR] System Health & Recovery Manager"""
    def __init__(self, kernel, service_id):
        super().__init__(kernel, service_id)
        self.patient_charts = {} # {service_id: {"last_beat": timestamp, "status": "healthy"}}
        self.check_interval = 10 # Cek setiap 10 detik

    def run_logic(self):
        """Loop Utama Dokter: Memantau detak jantung sistem"""
        self.logger.info("👨‍⚕️ VitalityService ON DUTY. Monitoring pulse...")

        self._inject_doctor_reference()

        while self.is_running:
            try:
                self._check_all_patients()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Doctor error during rounds: {e}")

    def _inject_doctor_reference(self):
        """Mendaftarkan diri ke setiap service sebagai dokter pribadi mereka"""
        count = 0
        services_to_check = getattr(self.kernel, 'services', {})

        for s_id, service in services_to_check.items():
            if hasattr(service, 'doctor'):
                service.doctor = self
                service.is_active_service = True
                self.patient_charts[s_id] = {"last_beat": time.time(), "status": "healthy"}
                count += 1

        if count > 0:
            self.logger.info(f"💉 Injected Doctor to {count} services.")

    def report_critical_failure(self, service_id, stack_trace):
        """Menerima panggilan darurat dari service yang sekarat"""
        self.logger.critical(f"🚑 EMERGENCY CALL from {service_id}!")

        self._notify_event_bus("SERVICE_CRITICAL_FAILURE", {
            "service_id": service_id,
            "error": str(stack_trace),
            "action": "CPR_INITIATED"
        })

        threading.Thread(target=self._perform_cpr, args=(service_id,), daemon=True).start()

    def _perform_cpr(self, service_id):
        """Logika Penyelamatan (Defibrillator)"""
        self.logger.info(f"⚡ Performing CPR on {service_id}...")

        try:
            services = getattr(self.kernel, 'services', {})
            patient = services.get(service_id)
            if patient and hasattr(patient, 'start'):
                if asyncio.iscoroutinefunction(patient.start):
                    pass # Butuh akses ke loop utama untuk restart async
                else:
                    patient.start()
                self.logger.info(f"✅ CPR Successful for {service_id}")
            else:
                self.logger.warning(f"❌ CPR Failed: No recovery path for {service_id}")
        except Exception as e:
            self.logger.error(f"❌ CPR Error for {service_id}: {e}")

    def _check_all_patients(self):
        """Memastikan semua organ masih bernapas"""
        for s_id, chart in self.patient_charts.items():
            if time.time() - chart["last_beat"] > 30:
                if chart["status"] != "distress":
                    chart["status"] = "distress"
                    self.logger.warning(f"⚠️ Service '{s_id}' is unresponsive (Flatline detected).")
                    self._notify_event_bus("SERVICE_HEALTH_UPDATE", {
                        "service_id": s_id, "status": "unresponsive"
                    })

    def _notify_event_bus(self, event, data):
        """Mengirim data kesehatan ke Saraf Pusat"""
        try:
            eb = Singleton.get_instance("event_bus")
            if eb:
                eb.publish(event, data, publisher_id="vitality_service")
        except: pass
