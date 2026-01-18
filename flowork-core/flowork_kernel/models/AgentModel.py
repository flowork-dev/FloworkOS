########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\models\AgentModel.py total lines 17 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
class AgentModel(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = ""
    brain_model_id: str = Field(..., description="The ID of the GGUF model file that acts as the agent's brain.")
    tool_ids: List[str] = Field(default_factory=list, description="A list of module_ids that this agent is allowed to use as tools.")
    prompt_template: Optional[str] = ""
