########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\agent_executor_service.py total lines 709 
########################################################################

import threading
import json
import time
import re
import os
import asyncio
import uuid
from typing import Callable, Awaitable, List, Dict, Any, Optional
from ..base_service import BaseService
from flowork_kernel.services.semantic_search_service.semantic_search_service import SemanticSearchService
from flowork_kernel.singleton import Singleton
from flowork_kernel.swarm import LocalSwarmRegistry, SwarmCoordinator
from flowork_kernel.context import boot_agent, AgentContext
from flowork_kernel.fac_enforcer import FacRuntime
from flowork_kernel.exceptions import PermissionDeniedError


class AgentExecutorService(BaseService):
    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.module_manager = self.kernel.get_service("module_manager_service")
        self.plugin_manager_service = self.kernel.get_service("plugin_manager_service")
        self.tools_manager_service = self.kernel.get_service("tools_manager_service")
        self.workflow_executor = self.kernel.get_service("workflow_executor_service")
        self.ai_manager = self.kernel.get_service("ai_provider_manager_service")
        self.event_bus = self.kernel.get_service("event_bus")
        self.semantic_search = Singleton.get_instance(SemanticSearchService)
        self.sessions = {}
        self.session_locks = {}

        self.active_tasks = {}

        self.local_swarm_registry = LocalSwarmRegistry()
        self.local_swarm_coordinator = SwarmCoordinator(
            send_task_fn=self.local_swarm_registry.make_send_task_fn(),
            default_timeout_s=60.0,
            retries=1,
            backoff_base_s=0.5
        )

        from flowork_kernel.services.gateway_connector_service.gateway_connector_service import GatewayConnectorService
        self.gateway_connector: GatewayConnectorService = self.kernel.get_service("gateway_connector_service")
        if self.gateway_connector and hasattr(self.gateway_connector, 'send_gateway_swarm_task'):
            self.gateway_swarm_coordinator = SwarmCoordinator(
                send_task_fn=self.gateway_connector.send_gateway_swarm_task,
                default_timeout_s=120.0,
                retries=1,
                backoff_base_s=1.0
            )
            self.logger.info("(R6) Multi-Node Gateway Swarm Coordinator has been initialized.")
        else:
            self.gateway_swarm_coordinator = None
            self.logger.warning("(R6) Multi-Node Swarm disabled: GatewayConnectorService not found or is missing 'send_gateway_swarm_task'.")

        self.logger.debug("Service 'AgentExecutor' initialized.")

    async def start_task(self, instruction: str, tools: List[str], user_id: str) -> str:
        """
        Memulai task agent secara asynchronous (Fire-and-forget).
        """
        task_id = str(uuid.uuid4())
        self.logger.info(f"[AgentExecutor] Starting Ad-hoc Task {task_id} for user {user_id}. Instruction: {instruction[:50]}...")

        self.active_tasks[task_id] = {
            "status": "running",
            "instruction": instruction,
            "logs": [],
            "result": None
        }

        asyncio.create_task(self._run_agent_loop(task_id, instruction, tools))

        return task_id

    async def _run_agent_loop(self, task_id: str, instruction: str, tools: List[str]):
        """
        [PHASE 3] The Brain Loop (ReAct Pattern Sederhana)
        """
        try:
            self.logger.info(f"[Task {task_id}] Thinking...")

            prompt = f"""
            You are a helpful AI Agent.
            User Request: {instruction}

            Available Tools: {', '.join(tools)}

            Thought Process:
            1. Analyze the request.
            2. Pick a tool if needed.
            3. Output JSON: {{ "action": "tool_name", "args": {{...}} }} OR {{ "action": "finish", "response": "..." }}
            """


            await asyncio.sleep(1)

            action = "finish"
            response_text = f"I have processed your request: '{instruction}'. Since I am in Beta, I simulated the execution using tools: {tools}."

            if "email" in instruction.lower() and "email_sender" in tools:
                action = "email_sender"
                self.logger.info(f"[Task {task_id}] Executing Tool: email_sender")
                await asyncio.sleep(1)
                response_text = "Email sent successfully (Simulated)."

            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["result"] = response_text

            if self.event_bus:
                self.event_bus.publish("AGENT_TASK_UPDATE", {
                    "task_id": task_id,
                    "status": "completed",
                    "output": response_text
                })

            self.logger.info(f"[Task {task_id}] Finished. Result: {response_text}")

        except Exception as e:
            self.logger.error(f"[Task {task_id}] Failed: {e}", exc_info=True)
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)


    async def execute_remote_swarm_task(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:

        try:
            tool_id = task_payload.get('tool_id')
            if not tool_id:
                return {"error": "EngineError (Worker): Remote task missing 'tool_id'"}

            self.logger.info(f"[RemoteSwarmWorker] Received task {task_payload.get('task_id')} for tool: {tool_id}")

            node_data = self._find_tool_manifest_as_node(tool_id)
            if not node_data:
                self.logger.error(f"[RemoteSwarmWorker] Tool '{tool_id}' not found on this worker engine.")
                return {"error": f"EngineError (Worker): Tool '{tool_id}' not found on this worker engine."}

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                self.workflow_executor.execute_workflow_synchronous,
                {node_data['id']: node_data},
                {},
                task_payload,
                self.logger.debug,
                lambda a,b,c: self.logger.debug(f"[RemoteSwarm] Tool Status: {b} - {c}"),
                f"remote_swarm_task_{task_payload.get('task_id')}",
                'EXECUTE',
                None
            )

            if isinstance(result, Exception):
                raise result

            if isinstance(result, dict) and "payload" in result:
                self.logger.info(f"[RemoteSwarmWorker] Task {task_payload.get('task_id')} completed successfully.")
                return result["payload"]

            self.logger.warning(f"[RemoteSwarmWorker] Tool {tool_id} ran but returned invalid structure.")
            return {"error": "EngineError (Worker): Tool executed but returned invalid structure."}

        except Exception as e:
            self.logger.error(f"[RemoteSwarmWorker] Task {task_payload.get('task_id')} FAILED: {e}", exc_info=True)
            return {"error": f"EngineError (Worker): {e}"}

    def _find_tool_manifest_as_node(self, component_id: str) -> Dict[str, Any] | None:

        manifest = None
        if self.module_manager:
            manifest = self.module_manager.get_manifest(component_id)
        if not manifest and self.plugin_manager_service:
            manifest = self.plugin_manager_service.get_manifest(component_id)
        if not manifest and self.tools_manager_service:
            manifest = self.tools_manager_service.get_manifest(component_id)

        if manifest:
            return {
                "id": component_id,
                "module_id": component_id,
                "manifest": manifest,
                "config_values": {}
            }
        return None

    def run_dynamic_agent_synchronous(self, initial_payload: dict, full_prompt_template: str, connected_tools: list, ai_brain_endpoint: str, status_updater, host_node_id: str):
        self.logger.info(f"Starting synchronous dynamic agent run for host node {host_node_id}.")

        agent_context: AgentContext = None
        agent_run_id = f"agent_host_run_{host_node_id}"
        try:
            fac_data = initial_payload.get("data", {}).get("fac_contract")
            if not fac_data:
                fac_data = {"id": "legacy_fac", "gas_limit": 10000}
                self.logger.warning(f"Agent {agent_run_id} starting with legacy FAC. R5 features (gas/permissions) may be limited.")

            agent_context = boot_agent(
                agent_id=agent_run_id,
                fac_data=fac_data
            )
            self.logger.info(f"(R6 PATCH) AgentContext booted. Timeline active for {agent_run_id}.")
        except Exception as e:
            self.logger.error(f"(R6 PATCH) CRITICAL: Failed to boot AgentContext: {e}", exc_info=True)
            pass

        current_payload = initial_payload.copy()
        if 'data' not in current_payload or not isinstance(current_payload['data'], dict):
            current_payload['data'] = {}
        conversation_history = []
        last_observation = "No actions taken yet."
        max_steps = 10

        self._register_tools_for_swarm(
            swarm_registry=self.local_swarm_registry,
            tools_list=connected_tools,
            base_payload=current_payload,
            workflow_context_id=host_node_id
        )

        if agent_context and agent_context.timeline:
            self.local_swarm_coordinator.timeline = agent_context.timeline
            self.logger.info(f"(R6 PATCH) Timeline hook injected into LocalSwarmCoordinator.")
            if self.gateway_swarm_coordinator:
                self.gateway_swarm_coordinator.timeline = agent_context.timeline
                self.logger.info(f"(R6) Timeline hook injected into GatewaySwarmCoordinator.")

        tools_for_agent = self._build_agent_tool_list(connected_tools)
        tools_prompt_string = self._get_tools_prompt_from_manifests(tools_for_agent)


        objective = current_payload.get('data', {}).get('prompt', 'No objective provided in payload.')

        try:
            for i in range(max_steps):
                status_updater(f"Cycle {i+1}/{max_steps}: Thinking...", "INFO")
                if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"🤔 Thinking...\n(Cycle {i+1}/{max_steps})"})
                prompt_to_brain = full_prompt_template
                prompt_to_brain = prompt_to_brain.replace('{objective}', objective)
                prompt_to_brain = prompt_to_brain.replace('{tools_string}', tools_prompt_string)
                prompt_to_brain = prompt_to_brain.replace('{history}', json.dumps(conversation_history, indent=2))
                prompt_to_brain = prompt_to_brain.replace('{last_observation}', last_observation)
                self.logger.debug(f"Sending prompt to brain: {ai_brain_endpoint}")
                ai_response = self.ai_manager.query_ai_by_task('text', prompt_to_brain, endpoint_id=ai_brain_endpoint)
                if "error" in ai_response:
                    last_observation = f"AI Brain Error: {ai_response['error']}"
                    self.logger.error(f"Error during agent cycle: {last_observation}")
                    conversation_history.append({"role": "user", "content": f"Observation: {last_observation}"})
                    if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"❌ Brain Error:\n{ai_response['error']}"})
                    continue
                action_json_str = ai_response.get('data', '{}')
                self.logger.debug(f"Brain response received: {action_json_str}")
                try:
                    json_match = re.search(r'\{[\s\S]*\}', action_json_str)
                    if not json_match:
                        raise json.JSONDecodeError("No valid JSON object found in the AI's response.", action_json_str, 0)
                    clean_json_str = json_match.group(0)
                    action_data = json.loads(clean_json_str)
                    thought = action_data.get("thought", action_data.get("thoughts", "No thought provided."))
                    action = action_data.get("action", {})
                    tool_to_use = action.get("tool_id")
                    tool_data = action.get("data", {})
                    conversation_history.append({"role": "assistant", "content": action_json_str})
                    status_updater(f"Thought: {thought}", "INFO")
                    if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"💡 Thought:\n{thought}"})
                    if tool_to_use == "finish":
                        final_answer = action.get('final_answer', "Objective complete.")
                        status_updater(f"Agent decided the objective is complete.", "SUCCESS")
                        if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"✅ Finished:\n{final_answer}"})

                        if agent_context:
                            pass

                        return final_answer, conversation_history
                    if not tool_to_use:
                        raise ValueError("AI brain failed to select a valid tool.")

                    if tool_to_use == "swarm_fan_out":
                        status_updater(f"Action: Using Swarm Fan-Out (Local)...", "INFO")
                        if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"🚀 SWARM (Local): Starting parallel fan-out..."})

                        swarm_engine_ids = tool_data.get("engine_ids", [])
                        swarm_task = tool_data.get("task", {})
                        swarm_quorum = tool_data.get("quorum", "all")

                        swarm_result = self.local_swarm_coordinator.fan_out(
                            engine_ids=swarm_engine_ids,
                            task=swarm_task,
                            quorum=swarm_quorum
                        )

                        last_observation = json.dumps(swarm_result, default=str)
                        conversation_history.append({"role": "user", "content": f"Observation: {last_observation}"})
                        if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"🏁 SWARM (Local) Complete:\n{swarm_result.get('summary')}"})
                        continue

                    elif tool_to_use == "swarm_fan_out_gateway":
                        status_updater(f"Action: Using Swarm Fan-Out (Gateway)...", "INFO")
                        if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"🌐 SWARM (Gateway): Starting multi-node fan-out..."})

                        if not self.gateway_swarm_coordinator:
                            raise Exception("GatewaySwarmCoordinator is not available (Gateway not connected?)")

                        swarm_engine_ids = tool_data.get("engine_ids", [])
                        swarm_task = tool_data.get("task", {})
                        swarm_quorum = tool_data.get("quorum", "all")


                        async def _run_gateway_swarm():
                            swarm_task["swarm_timeout_s"] = self.gateway_swarm_coordinator.default_timeout_s
                            return await self.gateway_swarm_coordinator.fan_out(
                                engine_ids=swarm_engine_ids,
                                task=swarm_task,
                                quorum=swarm_quorum
                            )

                        try:
                            main_loop = asyncio.get_running_loop()
                            future = asyncio.run_coroutine_threadsafe(_run_gateway_swarm(), main_loop)
                            swarm_result = future.result(timeout=130)
                        except Exception as e:
                            self.logger.error(f"[Gateway R6] Failed to run run_coroutine_threadsafe: {e}", exc_info=True)
                            raise Exception(f"Failed to execute Gateway Swarm: {e}")

                        last_observation = json.dumps(swarm_result, default=str)
                        conversation_history.append({"role": "user", "content": f"Observation: {last_observation}"})
                        if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"🏁 SWARM (Gateway) Complete:\n{swarm_result.get('summary')}"})
                        continue

                    status_updater(f"Action: Using tool '{tool_to_use}'", "INFO")
                    if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"🛠️ Using Tool: {tool_to_use}\nData: {json.dumps(tool_data, indent=2)}"})

                    node_to_run = next((t for t in tools_for_agent if t.get('id') == tool_to_use), None)
                    if not node_to_run:
                        raise ValueError(f"Tool '{tool_to_use}' was chosen by the AI, but it is not connected to the Agent Host.")

                    if self.event_bus: self.event_bus.publish("AGENT_HOST_TOOL_HIGHLIGHT", {"tool_node_id": node_to_run['id'], "host_node_id": host_node_id})
                    time.sleep(0.5)
                    payload_for_tool = current_payload.copy()
                    if 'data' not in payload_for_tool or not isinstance(payload_for_tool.get('data'), dict):
                        payload_for_tool['data'] = {}
                    payload_for_tool['data'].update(tool_data)

                    result_from_tool = self.workflow_executor.execute_workflow_synchronous(
                        nodes={node_to_run['id']: node_to_run},
                        connections={},
                        initial_payload=payload_for_tool,
                        logger=self.logger.debug,
                        status_updater=lambda a,b,c: self.logger.debug(f"Tool Status Update: {b} - {c}"),
                        workflow_context_id=f"agent_host_step_{i}",
                        mode='EXECUTE',
                        job_status_updater=None
                    )
                    if isinstance(result_from_tool, Exception):
                        raise result_from_tool
                    if isinstance(result_from_tool, dict) and "payload" in result_from_tool:
                        current_payload = result_from_tool["payload"]
                    last_observation = json.dumps(current_payload, default=str)
                    conversation_history.append({"role": "user", "content": f"Observation: {last_observation}"})
                except Exception as e:
                    last_observation = f"An error occurred: {e}"
                    self.logger.error(f"Error during agent cycle: {e}")
                    conversation_history.append({"role": "user", "content": f"Observation: {last_observation}"})
                    if self.event_bus: self.event_bus.publish("AGENT_HOST_DISPLAY_UPDATE", {"node_id": host_node_id, "text": f"❌ Error:\n{e}"})

            if agent_context:
                pass
            return "Max steps reached.", conversation_history

        finally:
            if agent_context:
                try:
                    agent_context.http_client.close()
                    agent_context.timeline.close()
                    self.logger.info(f"(R6 PATCH) AgentContext for {agent_run_id} cleaned up.")
                except Exception as e:
                    self.logger.warning(f"(R6 PATCH) Error cleaning up AgentContext: {e}")
            self.local_swarm_coordinator.timeline = None
            if self.gateway_swarm_coordinator:
                self.gateway_swarm_coordinator.timeline = None


    def _build_agent_tool_list(self, connected_tools: list) -> list:

        tools_for_agent = []
        plugin_manager = self.kernel.get_service("plugin_manager_service")

        for node_data in connected_tools:
            manifest = None
            component_id = node_data.get('module_id')
            if self.module_manager:
                manifest = self.module_manager.get_manifest(component_id)
            if not manifest and plugin_manager:
                manifest = plugin_manager.get_manifest(component_id)

            if manifest:
                full_tool_data = {**manifest, **node_data}
                tools_for_agent.append(full_tool_data)

        tools_for_agent.append({
            "id": "swarm_fan_out",
            "name": "Swarm Fan-Out (Local)",
            "description": "Executes a task in parallel on *local tools* on *this* engine. 'engine_ids' is a list of *tool_ids* (e.g., ['http_fetch', 'fs_read']), 'task' is the payload for all of them.",
            "is_swarm_tool": True
        })

        if self.gateway_swarm_coordinator:
            tools_for_agent.append({
                "id": "swarm_fan_out_gateway",
                "name": "Swarm Fan-Out (Gateway / Multi-Node)",
                "description": "Executes a task in parallel on *other* engines via the Gateway. 'engine_ids' is a list of *real Engine IDs* (e.g., ['engine-id-A', 'engine-id-B']). 'task' is the payload, which *must* include the 'tool_id' you want those engines to run.",
                "is_swarm_tool": True
            })

        return tools_for_agent

    def _get_tools_prompt_from_manifests(self, tools_for_agent: list) -> str:

        tools_list = []
        for manifest in tools_for_agent:
            tools_list.append(
                f"- tool_id: {manifest.get('id')}\n   name: {manifest.get('name')}\n   description: {manifest.get('description')}"
            )
        return "\n".join(tools_list)

    def _register_tools_for_swarm(self, swarm_registry: LocalSwarmRegistry, tools_list: list, base_payload: dict, workflow_context_id: str):


        for node_data in tools_list:
            tool_id = node_data.get('module_id')
            if not tool_id:
                continue

            def create_tool_handler(node_info: dict, tool_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:

                def _tool_handler(task_payload: Dict[str, Any]) -> Dict[str, Any]:

                    self.logger.info(f"[SwarmWorker] Executing tool '{tool_name}' via local swarm...")
                    try:
                        payload_for_tool = base_payload.copy()
                        if 'data' not in payload_for_tool or not isinstance(payload_for_tool.get('data'), dict):
                            payload_for_tool['data'] = {}

                        payload_for_tool['data'].update(task_payload)

                        result = self.workflow_executor.execute_workflow_synchronous(
                            nodes={node_info['id']: node_info},
                            connections={},
                            initial_payload=payload_for_tool,
                            logger=self.logger.debug,
                            status_updater=lambda a,b,c: self.logger.debug(f"[SwarmWorker] Tool Status: {b} - {c}"),
                            workflow_context_id=f"{workflow_context_id}_swarm_task",
                            mode='EXECUTE',
                            job_status_updater=None
                        )

                        if isinstance(result, Exception):
                            raise result

                        if isinstance(result, dict) and "payload" in result:
                            return result["payload"]
                        return {"error": "Tool executed but returned invalid structure."}

                    except Exception as e:
                        self.logger.error(f"[SwarmWorker] Tool '{tool_name}' failed: {e}", exc_info=True)
                        return {"error": str(e)}

                return _tool_handler

            tool_handler_func = create_tool_handler(node_data, tool_id)
            swarm_registry.register(tool_id, tool_handler_func)
            self.logger.debug(f"[R6] Registered tool '{tool_id}' with LocalSwarmRegistry.")


    async def _run_session_logic(self, session_id: str, initial_intent: str, context: dict,
                                 emit_callback: Callable[[str, dict], Awaitable[None]],
                                 input_queue: asyncio.Queue,
                                 fac_rt: FacRuntime):
        self.logger.info(f"[AgentSession {session_id}] Task starting. Intent: {initial_intent[:50]}...")
        history = []

        try:
            await emit_callback('core:agent_status', {
                "session_id": session_id,
                "phase": "running"
            })

            ai_provider = self.ai_manager.get_default_provider('text')
            if not ai_provider:
                self.logger.error(f"[AgentSession {session_id}] No default 'text' AI provider found.")
                raise Exception("No default text AI provider is configured on this engine.")

            chat_session = ai_provider.create_chat_session(history=history)
            self.logger.info(f"[AgentSession {session_id}] Created chat session with provider: {ai_provider.provider_id}")

            current_input = initial_intent

            while True:
                if current_input:
                    try:
                        fac_rt.budget.consume(1)
                        self.logger.info(f"[AgentSession {session_id}] Gas charge OK. Remaining: {fac_rt.budget.remaining()}")
                    except (PermissionError, PermissionDeniedError) as e:
                        self.logger.warning(f"[AgentSession {session_id}] Gas limit exceeded: {e}")
                        await emit_callback('core:agent_error', {
                            "session_id": session_id,
                            "code": "GAS_LIMIT_EXCEEDED",
                            "message": f"Agent session has exceeded its gas limit: {e}"
                        })
                        break

                    self.logger.debug(f"[AgentSession {session_id}] Sending to AI: {current_input[:50]}...")
                    response_stream = None
                    full_response = ""
                    try:
                        response_stream = await chat_session.send_message_streaming_async(current_input)

                        async for chunk in response_stream:
                            if chunk:
                                full_response += chunk
                                await emit_callback('core:agent_token', {
                                    "session_id": session_id,
                                    "text": chunk
                                })

                        self.logger.debug(f"[AgentSession {session_id}] Full AI response: {full_response[:50]}...")

                    except Exception as e:
                        self.logger.error(f"[AgentSession {session_id}] AI streaming failed: {e}", exc_info=True)
                        await emit_callback('core:agent_error', {
                            "session_id": session_id,
                            "code": "AI_STREAM_ERROR",
                            "message": f"Error during AI streaming: {e}"
                        })

                self.logger.debug(f"[AgentSession {session_id}] Waiting for next user input...")
                next_input_data = await input_queue.get()

                if next_input_data is None:
                    self.logger.info(f"[AgentSession {session_id}] Received stop signal.")
                    break

                current_input = next_input_data.get('text')
                tool_response = next_input_data.get('tool')

                if tool_response:
                    self.logger.info(f"[AgentSession {session_id}] Received tool response: {tool_response.get('name')}")
                    current_input = f"Tool Response: {json.dumps(tool_response)}"

                elif not current_input:
                    self.logger.debug(f"[AgentSession {session_id}] Received empty input, waiting again.")
                    current_input = None
                    continue

        except asyncio.CancelledError:
            self.logger.info(f"[AgentSession {session_id}] Task was cancelled.")
            try:
                await emit_callback('core:agent_status', {
                    "session_id": session_id,
                    "phase": "cancelled"
                })
                await emit_callback('core:agent_done', {
                    "session_id": session_id,
                    "outcome": "cancelled"
                })
            except Exception:
                pass


        except Exception as e:
            self.logger.error(f"[AgentSession {session_id}] Session loop CRASHED: {e}", exc_info=True)
            try:
                await emit_callback('core:agent_error', {
                    "session_id": session_id,
                    "code": "SESSION_CRASH",
                    "message": str(e)
                })
            except Exception as e2:
                self.logger.error(f"[AgentSession {session_id}] FAILED TO SEND CRASH ERROR: {e2}")

        finally:
            if session_id in self.session_locks:
                async with self.session_locks[session_id]:
                    if session_id in self.sessions:
                        del self.sessions[session_id]
                del self.session_locks[session_id]

            self.logger.info(f"[AgentSession {session_id}] Task finished and cleaned up.")

    async def start_session(self, data: dict, emit_callback: Callable[[str, dict], Awaitable[None]], fac_rt: FacRuntime):
        session_id = data.get('session_id')
        intent = data.get('intent')
        context = data.get('context', {})

        if not session_id or not intent:
            self.logger.error(f"[AgentExecutor] Invalid start_session request. Missing session_id or intent.")
            await emit_callback('core:agent_error', {
                "session_id": session_id,
                "code": "INVALID_START",
                "message": "Core received invalid start request (missing session_id or intent)."
            })
            return

        if session_id in self.sessions:
                self.logger.warning(f"[AgentExecutor] Session {session_id} already exists. Attempting to cancel old one.")
                await self.cancel_session({"session_id": session_id})


        input_queue = asyncio.Queue()

        expires_at = fac_rt.fac_dict.get('expires_at')
        timeout_seconds = None
        if expires_at:
            timeout_seconds = max(1, expires_at - time.time())
            self.logger.info(f"[AgentSession {session_id}] FAC: Applying TTL. Timeout in {timeout_seconds:.2f}s.")

        self.logger.info(f"[AgentSession {session_id}] FAC: Applying Gas Limit of {fac_rt.budget.total} (from FacRuntime).")


        agent_task_logic = self._run_session_logic(
            session_id, intent, context, emit_callback, input_queue,
            fac_rt=fac_rt
        )

        async def session_wrapper():
            try:
                await asyncio.wait_for(
                    agent_task_logic,
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"[AgentSession {session_id}] Session timed out (TTL exceeded).")
                try:
                    await emit_callback('core:agent_error', {
                        "session_id": session_id,
                        "code": "AGENT_TIMED_OUT",
                        "message": "Agent session exceeded its time-to-live (TTL)."
                    })
                except Exception:
                    pass
            except asyncio.CancelledError:
                raise
            except Exception as e:
                self.logger.error(f"[AgentSession {session_id}] Session wrapper CRASHED: {e}", exc_info=True)
                try:
                    await emit_callback('core:agent_error', {
                        "session_id": session_id,
                        "code": "SESSION_WRAPPER_CRASH",
                        "message": str(e)
                    })
                except Exception:
                    pass
        agent_task = asyncio.create_task(session_wrapper())
        self.session_locks[session_id] = asyncio.Lock()
        async with self.session_locks[session_id]:
            self.sessions[session_id] = {
                "task": agent_task,
                "input_queue": input_queue,
                "emit_callback": emit_callback,
                "conversation_history": [],
                "last_observation": "No actions taken yet.",
                "objective": intent
            }

        self.logger.info(f"[AgentExecutor] Agent session {session_id} started in a new task.")
    async def cancel_session(self, data: dict):
        session_id = data.get('session_id')
        session_info = self.sessions.get(session_id)
        if session_info and session_info.get("task"):
            try:
                session_info["task"].cancel()
                self.logger.info(f"[AgentExecutor] Cancellation request sent to session task {session_id}.")
            except Exception as e:
                self.logger.error(f"[AgentExecutor] Error during task cancellation for {session_id}: {e}")
        else:
            self.logger.warning(f"[AgentExecutor] Could not cancel session {session_id}: Task not found.")
    async def handle_input(self, data: dict):
        session_id = data.get('session_id')
        payload = data.get('payload')

        fac_rt: Optional[FacRuntime] = None
        if self.gateway_connector:
            fac_rt = self.gateway_connector.g_active_sessions.get(session_id)

        if not fac_rt:
            self.logger.warning(f"[AgentExecutor] Input for {session_id} REJECTED: No valid FAC runtime found (session may have expired or failed start).")
            try:
                emit_callback = self.sessions.get(session_id, {}).get("emit_callback")
                if emit_callback:
                    await emit_callback('core:agent_error', {
                        'session_id': session_id,
                        'code': 'SESSION_INVALID',
                        'message': 'No valid session runtime found. Please restart session.'
                    })
            except Exception as e:
                self.logger.error(f"Failed to send session invalid error: {e}")
            return


        session_info = self.sessions.get(session_id)
        if session_info and session_info.get("input_queue"):
            await session_info["input_queue"].put(payload)
            self.logger.info(f"[AgentExecutor] Input queued for session {session_id}.")
        else:
            self.logger.warning(f"[AgentExecutor] Could not queue input for session {session_id}: Session not found or queue missing.")
