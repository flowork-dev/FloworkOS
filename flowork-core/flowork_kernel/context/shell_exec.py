########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\context\shell_exec.py total lines 77 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import httpx
import os
import json
import subprocess
from flowork_kernel.timeline import TimelineLogger
from flowork_kernel.episodic import EpisodicStore
from flowork_kernel.gremlin import maybe_chaos_inject

FacRuntime = FakeFacRuntime
FacEnforcer = FakeFacEnforcer
GAS_COSTS = {'HTTP_FETCH': 15, 'FS_READ_KB': 1, 'FS_WRITE_KB': 2, 'EPISODIC_WRITE': 5, 'EPISODIC_READ': 2, 'AGENT_TOOL_CALL': 10, 'SHELL_EXEC': 25}

def boot_agent(agent_id: str, fac_data: dict) -> AgentContext:
    try:
        fac_runtime = FacRuntime(fac_data)
        fac_runtime.validate_schema()
        fac_runtime.validate_ttl()
        fac_runtime.validate_signature()
    except Exception as e:
        print(f'FATAL BOOT ERROR (Agent: {agent_id}): FAC validation failed: {e}')
        raise ValueError(f'Agent {agent_id} boot failed: Invalid FAC.') from e
    try:
        fac_enforcer = FacEnforcer(fac_runtime)
    except Exception as e:
        print(f'FATAL BOOT ERROR (Agent: {agent_id}): FAC Enforcer init failed: {e}')
        raise ValueError(f'Agent {agent_id} boot failed: Invalid Enforcer.') from e
    try:
        timeline = TimelineLogger(agent_id)
        episodic = EpisodicStore(agent_id)
    except Exception as e:
        print(f'FATAL BOOT ERROR (Agent: {agent_id}): Failed to init context services: {e}')
        print(f'WARNING (R5): TimelineLogger/EpisodicStore init in boot_agent needs fixing.')
        print(f'WARNING (R5): TimelineLogger requires (base_path, namespace).')
        timeline = None
        episodic = None
        timeline = TimelineLogger(agent_id)
        episodic = EpisodicStore(agent_id)
    except Exception as e:
        print(f'FATAL BOOT ERROR (Agent: {agent_id}): Failed to init context services: {e}')
        try:
            timeline.close()
        except Exception:
            pass
        raise IOError(f'Agent {agent_id} boot failed: Cannot init services.') from e
    if timeline:
        timeline.log(event_type='agent_boot', data={'fac_id': fac_runtime.get_id(), 'gas_limit': fac_runtime.get_gas_limit()})
    context = AgentContext(agent_id=agent_id, fac_runtime=fac_runtime, fac_enforcer=fac_enforcer, timeline=timeline, episodic=episodic)
    return context

def run(hub, command: str) -> dict:
    hub.execute_sync('_enforce_permission', 'shell', command, 'shell_exec')
    maybe_chaos_inject('shell_exec')
    log_data = {'command': command}
    try:
        hub.execute_sync('_enforce_gas', GAS_COSTS['SHELL_EXEC'], 'shell_exec')
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, check=True)
        log_data['success'] = True
        log_data['return_code'] = result.returncode
        return {'stdout': result.stdout, 'stderr': result.stderr}
    except subprocess.TimeoutExpired as e:
        log_data['error'] = 'TimeoutExpired'
        raise Exception('Shell command timed out after 10 seconds') from e
    except subprocess.CalledProcessError as e:
        log_data['error'] = 'CalledProcessError'
        log_data['return_code'] = e.returncode
        return {'stdout': e.stdout, 'stderr': e.stderr}
    except Exception as e:
        log_data['error'] = str(e)
        raise
    finally:
        hub.timeline.log('shell_exec', log_data)
