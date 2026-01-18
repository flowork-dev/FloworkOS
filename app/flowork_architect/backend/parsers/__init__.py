########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\flowork_architect\backend\parsers\__init__.py total lines 28 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import importlib
import pkgutil
from .base import BaseParser

def load_parsers_map():
    parsers = []
    package_dir = os.path.dirname(__file__)

    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        if module_name == 'base': continue

        try:
            module = importlib.import_module(f".{module_name}", package=__package__)
            for attribute_name in dir(module):
                cls = getattr(module, attribute_name)
                if isinstance(cls, type) and issubclass(cls, BaseParser) and cls is not BaseParser:
                    parsers.append(cls())
        except Exception as e:
            print(f"[Cortex] Gagal load parser {module_name}: {e}")

    return sorted(parsers, key=lambda x: x.priority, reverse=True)
