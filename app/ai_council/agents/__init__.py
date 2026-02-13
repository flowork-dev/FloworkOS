########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\agents\__init__.py total lines 34 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import importlib
import pkgutil
import inspect
from .base import BaseAgent

def load_all_agents():
    """
    Dynamically scan and instantiate all agents in this directory.
    Returns a list of initialized Agent objects.
    """
    agents = []
    package_dir = os.path.dirname(__file__)

    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        if module_name == "base": continue # Skip the base interface

        try:
            module = importlib.import_module(f".{module_name}", package=__name__)

            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    agents.append(obj()) # Instantiate and add
                    print(f"✅ [Agent Loader] Loaded: {name}")
        except Exception as e:
            print(f"❌ [Agent Loader] Error loading {module_name}: {e}")

    return agents
