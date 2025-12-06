########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\plugins\agent_host\processor.py total lines 179 
########################################################################

import uuid
import json
import traceback
from flowork_kernel.api_contract import BaseModule, IExecutable, IDataPreviewer
from flowork_kernel.context import boot_agent, AgentContext

class AgentHost(BaseModule, IExecutable, IDataPreviewer):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.ai_manager = self.services.get("ai_provider_manager_service")

    def execute(self, payload: dict, config: dict, status_updater, mode='EXECUTE', **kwargs):
        if mode == "SIMULATE":
            status_updater("Simulating Agent Host execution...", "INFO")
            return {
                "payload": {
                    "data": {
                        "agent_final_answer": "Simulation: Agent objective completed successfully.",
                        "agent_interaction_log": ["Thought: Simulating...", "Action: Done"]
                    }
                },
                "output_name": "success"
            }

        prompt_text = payload.get("data", {}).get("prompt") or payload.get("prompt")

        fac_raw = config.get("fac_contract")
        fac_data = None

        if isinstance(fac_raw, str):
            try:
                fac_data = json.loads(fac_raw)
            except:
                fac_data = {"objective": fac_raw, "gas_limit": config.get("max_gas", 10)}
        else:
            fac_data = fac_raw

        ai_provider_id = config.get("ai_provider_id")

        if not prompt_text:
            msg = "No prompt found in payload. Ensure previous node sends 'data.prompt'."
            self.logger(msg, "WARN")
            status_updater(msg, "WARN")

        if not fac_data:
            return self._error("No FAC (Agent Contract) provided.", payload)

        if not self.ai_manager:
            if self.kernel:
                self.ai_manager = self.kernel.get_service("ai_provider_manager_service")

            if not self.ai_manager:
                return self._error("AI Provider Manager Service not available.", payload)

        agent_run_id = f"agent_run_{uuid.uuid4()}"
        status_updater(f"Booting Agent {agent_run_id[:8]}...", "INFO")

        agent_context: AgentContext = None

        try:
            if "gas_limit" not in fac_data:
                fac_data["gas_limit"] = config.get("max_gas", 10)

            agent_context = boot_agent(
                agent_id=agent_run_id,
                fac_data=fac_data
            )

            available_tools = [
                {
                    "name": "http_fetch",
                    "description": "Fetches data from a URL. (e.g., http_fetch(url='...'))",
                    "function": agent_context.http_fetch
                },
                {
                    "name": "fs_read",
                    "description": "Reads a file from the filesystem.",
                    "function": agent_context.fs_read
                },
                {
                    "name": "fs_write",
                    "description": "Writes content to a file.",
                    "function": agent_context.fs_write
                },
                {
                    "name": "shell_exec",
                    "description": "Executes a shell command.",
                    "function": agent_context.shell_exec
                },
                {
                    "name": "memory_save",
                    "description": "Saves data to episodic memory.",
                    "function": agent_context.episodic_write
                },
                {
                    "name": "memory_load",
                    "description": "Loads data from episodic memory.",
                    "function": agent_context.episodic_read
                }
            ]

            ai_provider = self.ai_manager.get_provider(ai_provider_id)
            if not ai_provider:
                status_updater(f"Provider '{ai_provider_id}' not found. Trying default...", "WARN")
                ai_provider = self.ai_manager.get_default_provider()

            if not ai_provider:
                raise ValueError(f"No valid AI Provider found for ID: {ai_provider_id}")

            status_updater(f"Agent running on {ai_provider_id}...", "INFO")

            final_prompt = prompt_text if prompt_text else fac_data.get("objective", "Perform task.")

            agent_response = ai_provider.chat_with_tools(
                prompt=final_prompt,
                tools=available_tools
            )

            final_gas = agent_context.fac_runtime.get_gas_spent()
            agent_context.timeline.log("agent_complete", {"gas_spent": final_gas})

            status_updater("Agent objective completed.", "SUCCESS")

            if "data" not in payload: payload["data"] = {}
            payload["data"]["agent_final_answer"] = agent_response
            payload["data"]["agent_interaction_log"] = agent_context.timeline.get_logs()
            payload["data"]["gas_spent"] = final_gas

            return {
                "payload": payload,
                "output_name": "success"
            }

        except PermissionError as e:
            err_msg = f"Agent Permission Denied: {e}"
            self.logger(err_msg, "ERROR")
            if agent_context:
                agent_context.timeline.log("agent_failed", {"reason": "PERMISSION_DENIED"})
            return self._error(err_msg, payload)

        except Exception as e:
            err_msg = f"Agent Crash: {str(e)}"
            trace = traceback.format_exc()
            self.logger(f"{err_msg}\n{trace}", "ERROR")

            if agent_context:
                agent_context.timeline.log("agent_failed", {"reason": "CRASH", "details": err_msg})

            return self._error(err_msg, payload)

        finally:
            if agent_context:
                if hasattr(agent_context, 'http_client') and agent_context.http_client:
                    agent_context.http_client.close()
                if hasattr(agent_context, 'timeline') and agent_context.timeline:
                    agent_context.timeline.close()

    def _error(self, msg, payload):
        if "data" not in payload: payload["data"] = {}
        payload["data"]["error"] = msg
        return {"payload": payload, "output_name": "error"}

    def get_data_preview(self, config: dict):
        provider = config.get("ai_provider_id", "Unknown")
        gas = config.get("max_gas", 10)
        return [{
            "status": "ready",
            "message": f"Agent ready on {provider}",
            "details": {"gas_limit": gas}
        }]
