########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\database_service\start.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

def run(hub):
    """
    Startup Sequence for Database Service.
    Fix: Menjalankan inisialisasi secara sekuensial untuk menghindari lock.
    """
    hub.logger.info('🧠 [DatabaseService] Initializing SQL Elite Engine...')

    hub.execute_sync('create_tables')

    hub.execute_sync('create_indexes')

    try:
        hub.execute_sync('maintenance_scheduler', interval_hours=24)
        hub.logger.info('🧪 [DatabaseService] Neural Metabolism loop activated.')
    except Exception as e:
        hub.logger.warning(f'⚠️ [DatabaseService] Metabolism ignition failed: {e}')

    hub.logger.info('✅ [DatabaseService] Neural Vault is ONLINE and OPTIMIZED.')
