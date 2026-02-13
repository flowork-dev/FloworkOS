########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\hardware_io_service\_scan_hardware_capabilities.py total lines 28 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import logging
from flowork_kernel.services.base_service import BaseService


def run(hub):
    """Mengecek akses ke hardware fisik (Kamera & Audio)"""
    hub.logger.info('🔍 Indra scanning for physical interfaces...')
    if os.path.exists('/dev/video0'):
        hub.available_sensors.append('camera_0')
        hub.logger.info('📸 Camera detected at /dev/video0')
    if os.path.exists('/proc/asound/cards'):
        try:
            with open('/proc/asound/cards', 'r') as f:
                cards = f.read()
                hub.audio_devices.append('system_audio')
                hub.logger.info(f'🔊 Audio Hardware Detected:\n{cards}')
        except Exception as e:
            hub.logger.error(f'🚫 Failed to read audio cards: {e}')
    else:
        hub.logger.info('🔇 No physical audio hardware detected in this sector.')
