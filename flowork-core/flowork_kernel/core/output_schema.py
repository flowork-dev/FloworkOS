########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\core\output_schema.py total lines 20 
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
