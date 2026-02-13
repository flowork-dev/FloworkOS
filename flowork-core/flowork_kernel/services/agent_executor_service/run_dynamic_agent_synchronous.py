########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\agent_executor_service\run_dynamic_agent_synchronous.py total lines 174 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import threading
import json
import time
import re
import os
import asyncio
import uuid
from typing import Callable, Awaitable, List, Dict, Any, Optional
from flowork_kernel.singleton import Singleton
from flowork_kernel.swarm import LocalSwarmRegistry, SwarmCoordinator
from flowork_kernel.context import boot_agent, AgentContext
from flowork_kernel.fac_enforcer import FacRuntime
from flowork_kernel.exceptions import PermissionDeniedError


def run(hub, initial_payload: dict, full_prompt_template: str, connected_tools: list, ai_brain_endpoint: str, status_updater, host_node_id: str):
    hub.logger.info(f'Starting synchronous dynamic agent run for host node {host_node_id}.')
    agent_context: AgentContext = None
    agent_run_id = f'agent_host_run_{host_node_id}'
    try:
        fac_data = initial_payload.get('data', {}).get('fac_contract')
        if not fac_data:
            fac_data = {'id': 'legacy_fac', 'gas_limit': 10000}
            hub.logger.warning(f'Agent {agent_run_id} starting with legacy FAC. R5 features (gas/permissions) may be limited.')
        agent_context = boot_agent(agent_id=agent_run_id, fac_data=fac_data)
        hub.logger.info(f'(R6 PATCH) AgentContext booted. Timeline active for {agent_run_id}.')
    except Exception as e:
        hub.logger.error(f'(R6 PATCH) CRITICAL: Failed to boot AgentContext: {e}', exc_info=True)
        pass
    current_payload = initial_payload.copy()
    if 'data' not in current_payload or not isinstance(current_payload['data'], dict):
        current_payload['data'] = {}
    conversation_history = []
    last_observation = 'No actions taken yet.'
    max_steps = 10
    hub.execute_sync('_register_tools_for_swarm', swarm_registry=self.local_swarm_registry, tools_list=connected_tools, base_payload=current_payload, workflow_context_id=host_node_id)
    if agent_context and agent_context.timeline:
        hub.local_swarm_coordinator.timeline = agent_context.timeline
        hub.logger.info(f'(R6 PATCH) Timeline hook injected into LocalSwarmCoordinator.')
        if hub.gateway_swarm_coordinator:
            hub.gateway_swarm_coordinator.timeline = agent_context.timeline
            hub.logger.info(f'(R6) Timeline hook injected into GatewaySwarmCoordinator.')
    tools_for_agent = hub.execute_sync('_build_agent_tool_list', connected_tools)
    tools_prompt_string = hub.execute_sync('_get_tools_prompt_from_manifests', tools_for_agent)
    objective = current_payload.get('data', {}).get('prompt', 'No objective provided in payload.')
    try:
        for i in range(max_steps):
            status_updater(f'Cycle {i + 1}/{max_steps}: Thinking...', 'INFO')
            if hub.event_bus:
                hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f'🤔 Thinking...\n(Cycle {i + 1}/{max_steps})'})
            prompt_to_brain = full_prompt_template
            prompt_to_brain = prompt_to_brain.replace('{objective}', objective)
            prompt_to_brain = prompt_to_brain.replace('{tools_string}', tools_prompt_string)
            prompt_to_brain = prompt_to_brain.replace('{history}', json.dumps(conversation_history, indent=2))
            prompt_to_brain = prompt_to_brain.replace('{last_observation}', last_observation)
            hub.logger.debug(f'Sending prompt to brain: {ai_brain_endpoint}')
            ai_response = hub.ai_manager.query_ai_by_task('text', prompt_to_brain, endpoint_id=ai_brain_endpoint)
            if 'error' in ai_response:
                last_observation = f"AI Brain Error: {ai_response['error']}"
                hub.logger.error(f'Error during agent cycle: {last_observation}')
                conversation_history.append({'role': 'user', 'content': f'Observation: {last_observation}'})
                if hub.event_bus:
                    hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f"❌ Brain Error:\n{ai_response['error']}"})
                continue
            action_json_str = ai_response.get('data', '{}')
            hub.logger.debug(f'Brain response received: {action_json_str}')
            try:
                json_match = re.search('\\{[\\s\\S]*\\}', action_json_str)
                if not json_match:
                    raise json.JSONDecodeError("No valid JSON object found in the AI's response.", action_json_str, 0)
                clean_json_str = json_match.group(0)
                action_data = json.loads(clean_json_str)
                thought = action_data.get('thought', action_data.get('thoughts', 'No thought provided.'))
                action = action_data.get('action', {})
                tool_to_use = action.get('tool_id')
                tool_data = action.get('data', {})
                conversation_history.append({'role': 'assistant', 'content': action_json_str})
                status_updater(f'Thought: {thought}', 'INFO')
                if hub.event_bus:
                    hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f'💡 Thought:\n{thought}'})
                if tool_to_use == 'finish':
                    final_answer = action.get('final_answer', 'Objective complete.')
                    status_updater(f'Agent decided the objective is complete.', 'SUCCESS')
                    if hub.event_bus:
                        hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f'✅ Finished:\n{final_answer}'})
                    if agent_context:
                        pass
                    return (final_answer, conversation_history)
                if not tool_to_use:
                    raise ValueError('AI brain failed to select a valid tool.')
                if tool_to_use == 'swarm_fan_out':
                    status_updater(f'Action: Using Swarm Fan-Out (Local)...', 'INFO')
                    if hub.event_bus:
                        hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f'🚀 SWARM (Local): Starting parallel fan-out...'})
                    swarm_engine_ids = tool_data.get('engine_ids', [])
                    swarm_task = tool_data.get('task', {})
                    swarm_quorum = tool_data.get('quorum', 'all')
                    swarm_result = hub.local_swarm_coordinator.fan_out(engine_ids=swarm_engine_ids, task=swarm_task, quorum=swarm_quorum)
                    last_observation = json.dumps(swarm_result, default=str)
                    conversation_history.append({'role': 'user', 'content': f'Observation: {last_observation}'})
                    if hub.event_bus:
                        hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f"🏁 SWARM (Local) Complete:\n{swarm_result.get('summary')}"})
                    continue
                elif tool_to_use == 'swarm_fan_out_gateway':
                    status_updater(f'Action: Using Swarm Fan-Out (Gateway)...', 'INFO')
                    if hub.event_bus:
                        hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f'🌐 SWARM (Gateway): Starting multi-node fan-out...'})
                    if not hub.gateway_swarm_coordinator:
                        raise Exception('GatewaySwarmCoordinator is not available (Gateway not connected?)')
                    swarm_engine_ids = tool_data.get('engine_ids', [])
                    swarm_task = tool_data.get('task', {})
                    swarm_quorum = tool_data.get('quorum', 'all')

                    async def _run_gateway_swarm():
                        swarm_task['swarm_timeout_s'] = hub.gateway_swarm_coordinator.default_timeout_s
                        return await hub.gateway_swarm_coordinator.fan_out(engine_ids=swarm_engine_ids, task=swarm_task, quorum=swarm_quorum)
                    try:
                        main_loop = asyncio.get_running_loop()
                        future = asyncio.run_coroutine_threadsafe(_run_gateway_swarm(), main_loop)
                        swarm_result = future.result(timeout=130)
                    except Exception as e:
                        hub.logger.error(f'[Gateway R6] Failed to run run_coroutine_threadsafe: {e}', exc_info=True)
                        raise Exception(f'Failed to execute Gateway Swarm: {e}')
                    last_observation = json.dumps(swarm_result, default=str)
                    conversation_history.append({'role': 'user', 'content': f'Observation: {last_observation}'})
                    if hub.event_bus:
                        hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f"🏁 SWARM (Gateway) Complete:\n{swarm_result.get('summary')}"})
                    continue
                status_updater(f"Action: Using tool '{tool_to_use}'", 'INFO')
                if hub.event_bus:
                    hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f'🛠️ Using Tool: {tool_to_use}\nData: {json.dumps(tool_data, indent=2)}'})
                node_to_run = next((t for t in tools_for_agent if t.get('id') == tool_to_use), None)
                if not node_to_run:
                    raise ValueError(f"Tool '{tool_to_use}' was chosen by the AI, but it is not connected to the Agent Host.")
                if hub.event_bus:
                    hub.event_bus.publish('AGENT_HOST_TOOL_HIGHLIGHT', {'tool_node_id': node_to_run['id'], 'host_node_id': host_node_id})
                time.sleep(0.5)
                payload_for_tool = current_payload.copy()
                if 'data' not in payload_for_tool or not isinstance(payload_for_tool.get('data'), dict):
                    payload_for_tool['data'] = {}
                payload_for_tool['data'].update(tool_data)
                result_from_tool = hub.workflow_executor.execute_workflow_synchronous(nodes={node_to_run['id']: node_to_run}, connections={}, initial_payload=payload_for_tool, logger=hub.logger.debug, status_updater=lambda a, b, c: hub.logger.debug(f'Tool Status Update: {b} - {c}'), workflow_context_id=f'agent_host_step_{i}', mode='EXECUTE', job_status_updater=None)
                if isinstance(result_from_tool, Exception):
                    raise result_from_tool
                if isinstance(result_from_tool, dict) and 'payload' in result_from_tool:
                    current_payload = result_from_tool['payload']
                last_observation = json.dumps(current_payload, default=str)
                conversation_history.append({'role': 'user', 'content': f'Observation: {last_observation}'})
            except Exception as e:
                last_observation = f'An error occurred: {e}'
                hub.logger.error(f'Error during agent cycle: {e}')
                conversation_history.append({'role': 'user', 'content': f'Observation: {last_observation}'})
                if hub.event_bus:
                    hub.event_bus.publish('AGENT_HOST_DISPLAY_UPDATE', {'node_id': host_node_id, 'text': f'❌ Error:\n{e}'})
        if agent_context:
            pass
        return ('Max steps reached.', conversation_history)
    finally:
        if agent_context:
            try:
                agent_context.http_client.close()
                agent_context.timeline.close()
                hub.logger.info(f'(R6 PATCH) AgentContext for {agent_run_id} cleaned up.')
            except Exception as e:
                hub.logger.warning(f'(R6 PATCH) Error cleaning up AgentContext: {e}')
        hub.local_swarm_coordinator.timeline = None
        if hub.gateway_swarm_coordinator:
            hub.gateway_swarm_coordinator.timeline = None
