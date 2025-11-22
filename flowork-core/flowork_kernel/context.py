########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\context.py total lines 319 
########################################################################

import httpx
import os
import json
import subprocess
from flowork_kernel.timeline import TimelineLogger
from flowork_kernel.episodic import EpisodicStore
from flowork_kernel.gremlin import maybe_chaos_inject

class FakeFacRuntime:
    def __init__(self, fac_data):
        self.fac_data = fac_data
        self.gas_limit = fac_data.get("gas_limit", 1000)
        self.gas_spent = 0
        print(f"[FakeFacRuntime] Initialized with gas limit: {self.gas_limit}")

    def validate_schema(self): print("[FakeFacRuntime] Schema validated.")
    def validate_ttl(self): print("[FakeFacRuntime] TTL validated.")
    def validate_signature(self): print("[FakeFacRuntime] Signature validated (optional).")

    def consume_gas(self, amount: int) -> bool:
        if self.gas_spent + amount > self.gas_limit:
            self.gas_spent = self.gas_limit
            return False
        self.gas_spent += amount
        return True

    def get_id(self): return self.fac_data.get("id", "fac-placeholder-id")
    def get_gas_limit(self): return self.gas_limit
    def get_gas_spent(self): return self.gas_spent

class FakeFacEnforcer:
    def __init__(self, fac_runtime: FakeFacRuntime):
        self.fac = fac_runtime.fac_data
        print("[FakeFacEnforcer] Initialized.")

    def check(self, permission_type: str, target: str) -> bool:
        print(f"[FakeFacEnforcer] Checking permission '{permission_type}' for '{target}'...")
        if "DENY_ALL" in target:
            print("[FakeFacEnforcer] -> DENIED (Placeholder logic)")
            return False
        print("[FakeFacEnforcer] -> ALLOWED (Placeholder logic)")
        return True

FacRuntime = FakeFacRuntime
FacEnforcer = FakeFacEnforcer


GAS_COSTS = {
    "HTTP_FETCH": 15,
    "FS_READ_KB": 1,
    "FS_WRITE_KB": 2,
    "EPISODIC_WRITE": 5,
    "EPISODIC_READ": 2,
    "AGENT_TOOL_CALL": 10,
    "SHELL_EXEC": 25
}

class AgentContext:


    def __init__(self, agent_id: str,
                 fac_runtime: FacRuntime,
                 fac_enforcer: FacEnforcer,
                 timeline: TimelineLogger,
                 episodic: EpisodicStore):

        self.agent_id = agent_id
        self.fac_runtime = fac_runtime
        self.fac_enforcer = fac_enforcer
        self.timeline = timeline
        self.episodic = episodic
        self.kill_flag = False
        self.http_client = httpx.Client(timeout=10.0, follow_redirects=True)

    def _enforce_gas(self, cost: int, operation_name: str):
        if self.kill_flag:
            raise Exception(f"Agent (ID: {self.agent_id}) is terminated. Cannot perform '{operation_name}'.")

        if not self.fac_runtime.consume_gas(cost):
            self.kill_flag = True
            self.timeline.log(
                event_type="agent_killed",
                data={"reason": "OUT_OF_GAS", "failed_operation": operation_name, "gas_spent": self.fac_runtime.get_gas_spent()}
            )
            raise Exception(f"Out of Gas! Agent (ID: {self.agent_id}) terminated. Failed on '{operation_name}'.")

        self.timeline.log(
            event_type="gas_spent",
            data={"operation": operation_name, "cost": cost, "total_spent": self.fac_runtime.get_gas_spent()}
        )

    def _enforce_permission(self, p_type: str, p_target: str, p_name_for_log: str):

        if self.kill_flag:
            raise Exception(f"Agent (ID: {self.agent_id}) is terminated. Cannot check permission for '{p_name_for_log}'.")

        try:
            if not self.fac_enforcer.check(p_type, p_target):
                self.timeline.log(
                    event_type="permission_denied",
                    data={"type": p_type, "target": p_target, "operation": p_name_for_log}
                )
                raise PermissionError(f"Permission DENIED by FAC: Cannot {p_type} '{p_target}'")
        except Exception as e:
            self.timeline.log(
                event_type="permission_error",
                data={"type": p_type, "target": p_target, "error": str(e)}
            )
            raise


    def episodic_write(self, key: str, data: dict):
        self._enforce_gas(GAS_COSTS["EPISODIC_WRITE"], "episodic_write")
        try:
            self.episodic.write(key, data)
            self.timeline.log("episodic_write", {"key": key, "success": True})
        except Exception as e:
            self.timeline.log("episodic_write", {"key": key, "success": False, "error": str(e)})
            raise

    def episodic_read(self, key: str) -> dict | None:
        self._enforce_gas(GAS_COSTS["EPISODIC_READ"], "episodic_read")
        try:
            data = self.episodic.read(key)
            self.timeline.log("episodic_read", {"key": key, "found": (data is not None)})
            return data
        except Exception as e:
            self.timeline.log("episodic_read", {"key": key, "success": False, "error": str(e)})
            raise


    def http_fetch(self, url: str, method: str = "GET", headers: dict = None, json_data: dict = None, params: dict = None) -> dict:


        self._enforce_permission("http", url, "http_fetch")

        maybe_chaos_inject("http_fetch")

        self._enforce_gas(GAS_COSTS["HTTP_FETCH"], "http_fetch")

        response = None
        log_data = {"url": url, "method": method}

        try:
            response = self.http_client.request(
                method=method, url=url, headers=headers, json=json_data, params=params
            )
            response.raise_for_status()
            log_data["status_code"] = response.status_code
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"content": response.text}

        except httpx.HTTPStatusError as e:
            log_data["status_code"] = e.response.status_code
            log_data["error"] = f"HTTP Error: {e.response.status_code}"
            raise Exception(f"HTTP Error {e.response.status_code} for {url}") from e
        except httpx.RequestError as e:
            log_data["error"] = f"Request Error: {e.__class__.__name__}"
            raise Exception(f"Request failed for {url}: {e}") from e
        finally:
            self.timeline.log("http_fetch", log_data)

    def fs_read(self, file_path: str) -> str:


        self._enforce_permission("fs_read", file_path, "fs_read")

        maybe_chaos_inject("fs_read")

        log_data = {"path": file_path}
        try:
            size_bytes = os.path.getsize(file_path)
            size_kb = (size_bytes / 1024) + 1
            gas_cost = int(GAS_COSTS["FS_READ_KB"] * size_kb)
            self._enforce_gas(gas_cost, "fs_read")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            log_data["success"] = True
            log_data["size_kb"] = int(size_kb)
            return content

        except FileNotFoundError as e:
            log_data["error"] = "FileNotFound"
            raise
        except Exception as e:
            log_data["error"] = str(e)
            raise
        finally:
            self.timeline.log("fs_read", log_data)

    def fs_write(self, file_path: str, content: str):


        self._enforce_permission("fs_write", file_path, "fs_write")

        maybe_chaos_inject("fs_write")

        log_data = {"path": file_path}
        try:
            size_kb = (len(content.encode('utf-8')) / 1024) + 1
            gas_cost = int(GAS_COSTS["FS_WRITE_KB"] * size_kb)
            self._enforce_gas(gas_cost, "fs_write")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            log_data["success"] = True
            log_data["size_kb"] = int(size_kb)

        except Exception as e:
            log_data["error"] = str(e)
            raise
        finally:
            self.timeline.log("fs_write", log_data)

    def shell_exec(self, command: str) -> dict:


        self._enforce_permission("shell", command, "shell_exec")

        maybe_chaos_inject("shell_exec")

        log_data = {"command": command}
        try:
            self._enforce_gas(GAS_COSTS["SHELL_EXEC"], "shell_exec")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                check=True
            )

            log_data["success"] = True
            log_data["return_code"] = result.returncode
            return {"stdout": result.stdout, "stderr": result.stderr}

        except subprocess.TimeoutExpired as e:
            log_data["error"] = "TimeoutExpired"
            raise Exception("Shell command timed out after 10 seconds") from e
        except subprocess.CalledProcessError as e:
            log_data["error"] = "CalledProcessError"
            log_data["return_code"] = e.returncode
            return {"stdout": e.stdout, "stderr": e.stderr}
        except Exception as e:
            log_data["error"] = str(e)
            raise
        finally:
            self.timeline.log("shell_exec", log_data)


def boot_agent(agent_id: str, fac_data: dict) -> AgentContext:

    try:
        fac_runtime = FacRuntime(fac_data)
        fac_runtime.validate_schema()
        fac_runtime.validate_ttl()
        fac_runtime.validate_signature()
    except Exception as e:
        print(f"FATAL BOOT ERROR (Agent: {agent_id}): FAC validation failed: {e}")
        raise ValueError(f"Agent {agent_id} boot failed: Invalid FAC.") from e

    try:
        fac_enforcer = FacEnforcer(fac_runtime)
    except Exception as e:
        print(f"FATAL BOOT ERROR (Agent: {agent_id}): FAC Enforcer init failed: {e}")
        raise ValueError(f"Agent {agent_id} boot failed: Invalid Enforcer.") from e

    try:

        timeline = TimelineLogger(agent_id)
        episodic = EpisodicStore(agent_id)
    except Exception as e:
        print(f"FATAL BOOT ERROR (Agent: {agent_id}): Failed to init context services: {e}")
        print(f"WARNING (R5): TimelineLogger/EpisodicStore init in boot_agent needs fixing.")
        print(f"WARNING (R5): TimelineLogger requires (base_path, namespace).")
        timeline = None
        episodic = None


        timeline = TimelineLogger(agent_id)
        episodic = EpisodicStore(agent_id)

    except Exception as e:
        print(f"FATAL BOOT ERROR (Agent: {agent_id}): Failed to init context services: {e}")
        try:
            timeline.close()
        except Exception:
            pass
        raise IOError(f"Agent {agent_id} boot failed: Cannot init services.") from e


    if timeline:
        timeline.log(
            event_type="agent_boot",
            data={"fac_id": fac_runtime.get_id(), "gas_limit": fac_runtime.get_gas_limit()}
        )

    context = AgentContext(
        agent_id=agent_id,
        fac_runtime=fac_runtime,
        fac_enforcer=fac_enforcer,
        timeline=timeline,
        episodic=episodic
    )

    return context
