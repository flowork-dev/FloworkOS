########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\singleton.py total lines 42 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import threading
import logging

logger = logging.getLogger("SingletonRegistry")

class Singleton(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super(Singleton, cls).__call__(*args, **kwargs)
                    cls._instances[cls] = instance
                    try:
                        logger.info(f"➕ [INSTANCE CREATED] Class: {cls.__name__}")
                    except:
                        pass
        return cls._instances[cls]

    @classmethod
    def set_instance(mcs, instance_class, instance):
        with mcs._lock:
            mcs._instances[instance_class] = instance
            try:
                name = instance_class if isinstance(instance_class, str) else instance_class.__name__
                logger.info(f"💉 [INJECTED] Service: {name}")
            except:
                print(f"[Singleton] Injected: {instance_class}")

    @classmethod
    def get_instance(mcs, instance_class):
        with mcs._lock:
            instance = mcs._instances.get(instance_class)
            return instance
