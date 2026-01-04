########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\models\ConnectionModel.py total lines 18 
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
