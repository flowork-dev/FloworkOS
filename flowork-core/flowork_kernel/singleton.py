########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\singleton.py total lines 28 
########################################################################

import threading
class Singleton(type):

    _instances = {}
    _lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    @classmethod
    def set_instance(mcs, instance_class, instance):

        with mcs._lock:
            if instance_class not in mcs._instances:
                mcs._instances[instance_class] = instance
    @classmethod
    def get_instance(mcs, instance_class):

        with mcs._lock:
            return mcs._instances.get(instance_class)
