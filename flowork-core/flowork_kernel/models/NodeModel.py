########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\models\NodeModel.py total lines 18 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
class NodeModel(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    name: str
    x: float
    y: float
    module_id: str
    description: Optional[str] = ""
    config_values: Dict[str, Any] = Field(default_factory=dict)
