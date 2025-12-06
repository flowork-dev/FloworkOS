########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\api_server_service\routes\agent_routes.py total lines 250 
########################################################################

from .base_api_route import BaseApiRoute
from aiohttp import web
import json
import asyncio

class AgentRoutes(BaseApiRoute):

    def register_routes(self):
        return {
            "GET /api/v1/agents": self.handle_get_agents,
            "GET /api/v1/agents/{agent_id}": self.handle_get_agent,
            "POST /api/v1/agents": self.handle_post_agents,
            "DELETE /api/v1/agents/{agent_id}": self.handle_delete_agent,
            "POST /api/v1/agents/{agent_id}/run": self.handle_run_agent,
            "GET /api/v1/agents/run/{run_id}": self.handle_get_agent_run_status,
            "POST /api/v1/agents/run/{run_id}/stop": self.handle_stop_agent_run,

            "POST /api/v1/agent/run": self.handle_run_agent_task_adhoc,

            "POST /api/v1/ai/chat/completions": self.handle_chat_completions,
        }

    async def handle_chat_completions(self, request):
        """
        Handles standard Chat Completions AND Neural Council Sessions.
        Streamed response compatible with Gateway.
        """
        try:
            body = await request.json()
        except:
            return self._json_response({"error": "Invalid JSON"}, status=400)

        if body.get('is_council'):
            return await self._stream_council_session(request, body)

        return await self._stream_standard_chat(request, body)

    async def _stream_council_session(self, request, body):
        """
        Orchestrates the Council Session and streams chunks back to Gateway.
        """
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
        await response.prepare(request)

        try:
            from flowork_kernel.services.ai_architect_service.council_orchestrator import CouncilOrchestrator

            orchestrator = CouncilOrchestrator()
            judge_id = body.get('judge_id')
            members = body.get('members', [])
            topic = body.get('topic') or body.get('prompt')

            iterator = orchestrator.stream_deliberation(judge_id, members, topic)

            for chunk_str in iterator:
                await response.write(chunk_str.encode('utf-8'))
                await asyncio.sleep(0.01)

        except Exception as e:
            err_msg = json.dumps({"type": "error", "message": str(e)}) + "\n"
            await response.write(err_msg.encode('utf-8'))

        await response.write_eof()
        return response

    async def _stream_standard_chat(self, request, body):
        """
        Basic implementation for standard chat.
        """
        provider_manager = getattr(self.service_instance, 'ai_provider_manager', None)

        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={'Content-Type': 'application/json'}
        )
        await response.prepare(request)

        if not provider_manager:
             err = json.dumps({"type": "error", "message": "AI Provider Service unavailable in Core."}) + "\n"
             await response.write(err.encode('utf-8'))
             await response.write_eof()
             return response

        model = body.get('model')
        messages = body.get('messages', [])
        prompt = body.get('prompt')

        if not prompt and messages:
            for m in reversed(messages):
                if m['role'] == 'user':
                    prompt = m['content']
                    break

        try:
            stream = provider_manager.stream_text(
                model_id=model,
                prompt=prompt,
                system_prompt="You are a helpful Flowork assistant.",
                temperature=0.7
            )

            for chunk in stream:
                data = json.dumps({"type": "content", "chunk": chunk}) + "\n"
                await response.write(data.encode('utf-8'))
                await asyncio.sleep(0.01)

        except Exception as e:
             err = json.dumps({"type": "error", "message": f"Core Error: {str(e)}"}) + "\n"
             await response.write(err.encode('utf-8'))

        await response.write_eof()
        return response


    async def handle_get_agents(self, request):
        agent_manager = self.service_instance.agent_manager
        if not agent_manager:
            return self._json_response(
                {"error": "AgentManagerService is not available due to license restrictions."},
                status=503,
            )
        agents = agent_manager.get_all_agents()
        return self._json_response(agents)

    async def handle_get_agent(self, request):
        agent_id = request.match_info.get("agent_id")
        agent_manager = self.service_instance.agent_manager
        if not agent_manager:
            return self._json_response(
                {"error": "AgentManagerService is not available due to license restrictions."},
                status=503,
            )
        agent = agent_manager.get_agent(agent_id)
        if agent:
            return self._json_response(agent)
        else:
            return self._json_response({"error": f"Agent with ID '{agent_id}' not found."}, status=404)

    async def handle_post_agents(self, request):
        agent_manager = self.service_instance.agent_manager
        if not agent_manager:
            return self._json_response(
                {"error": "AgentManagerService is not available due to license restrictions."},
                status=503,
            )
        body = await request.json()
        result = agent_manager.save_agent(body)
        if "error" in result:
            return self._json_response(result, status=400)
        else:
            return self._json_response(result, status=201)

    async def handle_delete_agent(self, request):
        agent_id = request.match_info.get("agent_id")
        agent_manager = self.service_instance.agent_manager
        if not agent_manager:
            return self._json_response(
                {"error": "AgentManagerService is not available due to license restrictions."},
                status=503,
            )
        if agent_manager.delete_agent(agent_id):
            return self._json_response(None, status=204)
        else:
            return self._json_response({"error": "Agent not found."}, status=404)

    async def handle_run_agent(self, request):
        agent_id = request.match_info.get("agent_id")
        agent_executor = self.service_instance.agent_executor
        if not agent_executor:
            return self._json_response(
                {"error": "AgentExecutorService is not available due to license restrictions."},
                status=503,
            )
        body = await request.json()
        if "objective" not in body:
            return self._json_response({"error": "Request must contain an 'objective'."}, status=400)
        result = agent_executor.run_agent(agent_id, body["objective"])
        if "error" in result:
            return self._json_response(result, status=409)
        else:
            return self._json_response(result, status=202)

    async def handle_get_agent_run_status(self, request):
        run_id = request.match_info.get("run_id")
        agent_executor = self.service_instance.agent_executor
        if not agent_executor:
            return self._json_response(
                {"error": "AgentExecutorService is not available due to license restrictions."},
                status=503,
            )
        status = agent_executor.get_run_status(run_id)
        if "error" in status:
            return self._json_response(status, status=404)
        else:
            return self._json_response(status)

    async def handle_stop_agent_run(self, request):
        run_id = request.match_info.get("run_id")
        agent_executor = self.service_instance.agent_executor
        if not agent_executor:
            return self._json_response(
                {"error": "AgentExecutorService is not available due to license restrictions."},
                status=503,
            )
        result = agent_executor.stop_agent_run(run_id)
        if "error" in result:
            return self._json_response(result, status=404)
        else:
            return self._json_response(result)

    async def handle_run_agent_task_adhoc(self, request):
        agent_executor = self.service_instance.agent_executor
        if not agent_executor:
            return self._json_response({"error": "AgentExecutorService unavailable."}, status=503)

        try:
            body = await request.json()
            instruction = body.get('instruction') or body.get('user_instruction')
            tools = body.get('tools', [])
            user_id = getattr(request, 'user_id', 'anonymous_dev')

            if not instruction:
                return self._json_response({"error": "Missing 'instruction'."}, status=400)

            if hasattr(agent_executor, 'start_task'):
                task_id = await agent_executor.start_task(instruction, tools, user_id=user_id)
                return self._json_response({"status": "started", "task_id": task_id}, status=202)
            else:
                return self._json_response(
                    {"error": "Engine update required: AgentExecutor missing 'start_task'."},
                    status=501
                )

        except Exception as e:
            return self._json_response({"error": str(e)}, status=500)
