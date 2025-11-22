########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\plugins\agent_host\processor.py total lines 117 
########################################################################

import uuid
from flowork_kernel.context import boot_agent, AgentContext
from flowork_kernel.services.base_service import BaseService

class Processor:

    def __init__(self, kernel_services: BaseService, manifest: dict):
        self.kernel = kernel_services
        self.manifest = manifest
        try:
            self.ai_manager = self.kernel.get_service("ai_provider_manager_service")
        except Exception as e:
            self.ai_manager = None
            print(f"CRITICAL: Failed to get ai_provider_manager_service: {e}")

    def process(self, inputs: dict, settings: dict, **kwargs) -> dict:
        prompt_text = inputs.get("prompt", {}).get("content")
        fac_data = settings.get("fac_contract")

        if not prompt_text:
            return {"error_output": {"content": "No prompt provided to Agent Host."}}

        if not fac_data:
            return {"error_output": {"content": "No FAC (Agent Contract) provided."}}

        if not self.ai_manager:
            return {"error_output": {"content": "AI Provider Manager Service not available."}}

        agent_run_id = f"agent_run_{uuid.uuid4()}"

        agent_context: AgentContext = None
        try:
            agent_context = boot_agent(
                agent_id=agent_run_id,
                fac_data=fac_data
            )

            available_tools = [
                {
                    "name": "http_fetch",
                    "description": "Fetches data from a URL. (e.g., http_fetch(url='https://api.example.com/data'))",
                    "function": agent_context.http_fetch
                },
                {
                    "name": "fs_read",
                    "description": "Reads a file from the filesystem. (e.g., fs_read(file_path='./data/file.txt'))",
                    "function": agent_context.fs_read
                },
                {
                    "name": "fs_write",
                    "description": "Writes content to a file. (e.g., fs_write(file_path='./output/report.txt', content='Hello World'))",
                    "function": agent_context.fs_write
                },
                {
                    "name": "shell_exec",
                    "description": "Executes a shell command. (e.g., shell_exec(command='ls -la'))",
                    "function": agent_context.shell_exec
                },
                {
                    "name": "save_to_memory",
                    "description": "Saves a JSON object to episodic memory. (e.g., save_to_memory(key='plan', data={'step': 1, 'goal': '...'}))",
                    "function": agent_context.episodic_write
                },
                {
                    "name": "load_from_memory",
                    "description": "Loads a JSON object from episodic memory. (e.g., load_from_memory(key='plan'))",
                    "function": agent_context.episodic_read
                }
            ]

            ai_provider = self.ai_manager.get_provider(settings.get("ai_provider_id"))
            if not ai_provider:
                raise ValueError(f"AI Provider '{settings.get('ai_provider_id')}' not found.")

            agent_response = ai_provider.chat_with_tools(
                prompt=prompt_text,
                tools=available_tools
            )

            final_gas_spent = agent_context.fac_runtime.get_gas_spent()
            agent_context.timeline.log("agent_complete", {"gas_spent": final_gas_spent})

            return {
                "response_output": {"content": agent_response},
                "final_gas_spent": final_gas_spent
            }

        except PermissionError as e:
            error_message = f"Agent Terminated (Permission Denied): {e}"
            print(f"ERROR: Agent Host (Run ID: {agent_run_id}) failed: {error_message}")
            if agent_context and agent_context.timeline:
                agent_context.timeline.log("agent_failed", {"error": error_message, "reason": "PERMISSION_DENIED"})
            return {"error_output": {"content": error_message}}

        except Exception as e:
            error_message = str(e)
            print(f"ERROR: Agent Host (Run ID: {agent_run_id}) failed: {error_message}")

            if agent_context and agent_context.timeline:
                reason = "OUT_OF_GAS" if agent_context.kill_flag else "AGENT_CRASH"
                agent_context.timeline.log("agent_failed", {"error": error_message, "reason": reason})

            return {"error_output": {"content": error_message}}

        finally:
            if agent_context:
                agent_context.http_client.close()
                agent_context.timeline.close()

    def on_node_deleted(self, settings: dict):
        pass
