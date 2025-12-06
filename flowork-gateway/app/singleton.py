########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\app\singleton.py total lines 42 
########################################################################

import threading
import typing as t
class SingletonMeta(type):

    _instances: t.Dict[t.Type, t.Any] = {}
    _lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
                    cls._instances[cls] = instance
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
class _GlobalHandle(metaclass=SingletonMeta):

    def set_instance(self, instance_class, instance):
        SingletonMeta.set_instance(instance_class, instance)
    def get_instance(self, instance_class):
        return SingletonMeta.get_instance(instance_class)
class Singleton:

    _handle = _GlobalHandle()
    def __new__(cls, *args, **kwargs):
        return cls._handle
__all__ = ["SingletonMeta", "Singleton"]
