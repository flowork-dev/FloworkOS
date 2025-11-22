########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\models\NodeModel.py total lines 18 
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
