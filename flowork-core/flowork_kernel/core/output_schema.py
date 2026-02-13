########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\core\output_schema.py total lines 20 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from typing import Dict, Any
class OutputVar:

    def __init__(self, display_name: str, var_type: str, description: str = ""):
        self.display_name = display_name
        self.var_type = var_type
        self.description = description
class OutputSchema:

    def __init__(self, variables: Dict[str, OutputVar]):
        self.variables = variables
def create_output_schema(**kwargs: OutputVar) -> OutputSchema:

    return OutputSchema(kwargs)
