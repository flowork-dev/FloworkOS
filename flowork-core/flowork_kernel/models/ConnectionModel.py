########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\models\ConnectionModel.py total lines 18 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
class ConnectionModel(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    source: UUID
    target: UUID
    source_port_name: Optional[str] = None
    target_port_name: Optional[str] = None
    class Config:
        allow_population_by_field_name = True
