########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\core\input_schema.py total lines 24 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from typing import Dict, Any
class InputVar:

    def __init__(self, display_name: str, var_type: str, required: bool = False, description: str = ""):
        self.display_name = display_name
        self.var_type = var_type
        self.required = required
        self.description = description
class InputSchema:

    def __init__(self, variables: Dict[str, InputVar]):
        self.variables = variables
    def get_var(self, key: str, payload: Dict[str, Any]) -> Any:

        return payload.get('data', {}).get(key)
def create_input_schema(**kwargs: InputVar) -> InputSchema:

    return InputSchema(kwargs)
