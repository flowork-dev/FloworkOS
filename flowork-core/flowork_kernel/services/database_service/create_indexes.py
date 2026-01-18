########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\create_indexes.py total lines 34 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import logging

def run(hub):
    """
    Optimasi Database: Membuat index pada tabel vital untuk akses kecepatan tinggi (0.001ms).
    Fokus pada tabel app_storage yang digunakan oleh jutaan user secara paralel.
    """
    try:
        with hub.execute_sync('transaction') as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_app_storage_composite
                ON app_storage (owner_app_id, key);
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_app_storage_key
                ON app_storage (key);
            ''')

            hub.logger.info("⚡ [SQL Elite] Database indexes verified/created successfully.")
            return True

    except Exception as e:
        if hasattr(hub, 'logger'):
            hub.logger.error(f"❌ [SQL Elite] Failed to create indexes: {e}")
        return False
