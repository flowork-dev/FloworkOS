########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_architect_service\ai_architect_service.py total lines 89 
########################################################################

import json
import os
import re
from ..base_service import BaseService

from .council_orchestrator import CouncilOrchestrator

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

class AiArchitectService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.module_manager = self.kernel.get_service("module_manager_service")
        self.ai_manager = self.kernel.get_service("ai_provider_manager_service")

        self.council = CouncilOrchestrator(self.kernel)

        self.logger.debug("Service 'AiArchitectService' initialized.")

    def _get_available_tools_prompt(self):
        if not self.module_manager:
            return "No tools available."
        tools = []
        for mod_id, mod_data in self.module_manager.loaded_modules.items():
            manifest = mod_data.get("manifest", {})
            if manifest.get("type") not in ["LOGIC", "ACTION", "CONTROL_FLOW"]:
                continue
            if "ui_provider" in manifest.get("permissions", []):
                continue
            tool_info = f"- module_id: {mod_id}\n  name: {manifest.get('name')}\n  description: {manifest.get('description')}"
            tools.append(tool_info)
        return "\n".join(tools)

    def generate_workflow_from_prompt(self, user_prompt: str):
        if not self.ai_manager:
            raise ConnectionError("AIProviderManagerService is not available.")

        available_tools = self._get_available_tools_prompt()

        system_prompt = f"""
You are the AI Architect of Flowork. Your job is to convert user requests into a JSON workflow structure.
Available Modules:
{available_tools}

Rules:
1. Return ONLY valid JSON. No markdown, no explanation.
2. The JSON must have "nodes" (list) and "connections" (list).
3. Use the module_ids provided above.
4. If uncertain, use 'python_script' node.
"""
        self.logger.info("AI Architect is consulting the default Text AI...")

        full_prompt = f"{system_prompt}\n\nUSER REQUEST: \"{user_prompt}\""

        response = self.ai_manager.query_ai_by_task('text', full_prompt)

        if "error" in response:
            raise ConnectionError(f"AI Architect failed: {response['error']}")

        response_text = response.get("data", "{}").strip()

        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise ValueError("No valid JSON object found in the AI's response.")

            json_string = json_match.group(0)
            workflow_graph = json.loads(json_string)

            if "nodes" not in workflow_graph or "connections" not in workflow_graph:
                raise ValueError("AI response is missing 'nodes' or 'connections' key.")

            self.logger.info("AI Architect successfully generated a workflow graph.")
            return workflow_graph

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"AI Architect failed to parse the LLM response: {e}\nRaw response: {response_text}")
            raise ValueError(f"The AI returned an invalid workflow structure. Raw Response: {response_text}. Error: {e}")
