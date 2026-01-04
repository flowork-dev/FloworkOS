########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\models\WorkflowPayloadModel.py total lines 12 
########################################################################

from pydantic import BaseModel, Field
from typing import Dict, Any, List
class WorkflowPayloadModel(BaseModel):

    data: Dict[str, Any] = Field(default_factory=dict)
    history: List[Any] = Field(default_factory=list)
