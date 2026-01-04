########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\capabilities\agent_run.py total lines 38 
########################################################################

from __future__ import annotations
from typing import Dict

class AgentRun:

    def __init__(self, scope: Dict[str, str]):

        if not isinstance(scope, dict):
             raise ValueError("agent.run scope must be a dictionary")

        self.engine_id = str(scope.get("engine_id", "")).strip()

        if not self.engine_id:
            raise ValueError("agent.run scope requires 'engine_id'")

    def permit_engine(self, engine_id_to_run: str) -> None:

        if self.engine_id == "*":
            return

        eid_to_run_str = str(engine_id_to_run).strip()

        if not self.engine_id or not eid_to_run_str:
            raise PermissionError("agent.run blocked: missing engine_id in scope or request")

        if self.engine_id != eid_to_run_str:
            raise PermissionError(
                f"agent.run blocked: FAC scope '{self.engine_id}' "
                f"mismatches requested engine '{eid_to_run_str}'"
            )

        return
