########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\app_manager_service\ensure_app_running.py total lines 111 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import sys
import subprocess
import time
import threading

_spawn_lock = threading.Lock()

async def run(hub, app_id: str, retry_count=0, user_id=None): # Added async for consistency
    """
    Ensures app runner is active with Immune System and Secret Injection.
    Fix: Proper routing to VariableManager for secret injection.
    """
    if not hasattr(hub, 'process_registry'): hub.process_registry = {}
    if not hasattr(hub, 'crash_tracker'): hub.crash_tracker = {}

    now = time.time()
    crash_info = hub.crash_tracker.get(app_id, {'count': 0, 'last_reset': now, 'quarantined': False})

    if crash_info['quarantined']:
        hub.logger.error(f"🛡️ [ImmuneSystem] {app_id} is in QUARANTINE. Manual fix needed.")
        raise Exception(f"App {app_id} is quarantined due to crash loop.")

    if now - crash_info['last_reset'] > 60:
        crash_info = {'count': 0, 'last_reset': now, 'quarantined': False}

    with _spawn_lock:
        if app_id in hub.process_registry:
            proc = hub.process_registry[app_id]
            if proc.poll() is None:
                try: hub.execute_sync('_touch_app_activity', app_id)
                except: pass
                return hub.execute_sync('get_assigned_port', app_id)

    port = hub.execute_sync('get_assigned_port', app_id)
    app_info = hub.registry['apps']['data'].get(app_id)
    if not app_info: raise Exception(f'App {app_id} manifest not found.')

    app_path = app_info['path']
    project_root = hub.kernel.project_root_path

    env_copy = os.environ.copy()
    config_file = os.path.join(app_path, 'config_schema.json')
    if os.path.exists(config_file) and user_id:
        try:
            with open(config_file, 'r') as f:
                schema = json.load(f)

                var_manager = hub.kernel.get_service('variable_manager')

                for var_meta in schema.get('variables', []):
                    key = var_meta['key']

                    val = None
                    if var_manager:
                        val = var_manager.get_variable(key, user_id=user_id)

                    if val:
                        env_copy[key] = str(val)
                        hub.logger.info(f"💉 [Syringe] Injected secret '{key}' for {app_id}")
        except Exception as e:
            hub.logger.warning(f"⚠️ [Syringe] Secret injection failed for {app_id}: {e}")

    env_copy['PYTHONPATH'] = f"{project_root}{os.pathsep}{env_copy.get('PYTHONPATH', '')}"
    runner_script = os.path.join(project_root, 'app', 'executor', 'runner.py')
    if not os.path.exists(runner_script): runner_script = '/app/app/executor/runner.py'

    lib_manager = hub.kernel.get_service('library_manager')
    lib_paths = []
    req_file = os.path.join(app_path, 'requirements.txt')
    if lib_manager and os.path.exists(req_file):
        lib_paths = lib_manager.resolve_dependencies(app_id, req_file)

    cmd = [sys.executable, runner_script, '--daemon', '--port', str(port), '--path', app_path, '--appid', app_id, '--libs', json.dumps(lib_paths)]

    try:
        with _spawn_lock:
            proc = subprocess.Popen(cmd, cwd=project_root, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env_copy, text=True)
            hub.process_registry[app_id] = proc
            if not hasattr(hub, 'instances'): hub.instances = {}
            hub.instances[app_id] = {'started_at': time.time(), 'pid': proc.pid}

        hub.logger.info(f'🚀 [AppManager] Spawned Daemon for {app_id} (PID: {proc.pid})')
        time.sleep(1.5)

        if proc.poll() is not None:
            raw_error = proc.stderr.read()

            if "ModuleNotFoundError" in raw_error and retry_count < 1:
                hub.logger.warning(f"📦 [Auto-Heal] Library missing for {app_id}. Triggering surgery...")
                if lib_manager:
                    lib_manager.resolve_dependencies(app_id, req_file, force_reinstall=True)
                    return await run(hub, app_id, retry_count + 1, user_id) # FIX ASYNC

            crash_info['count'] += 1
            if crash_info['count'] > 3:
                crash_info['quarantined'] = True
            hub.crash_tracker[app_id] = crash_info
            raise Exception(f'App {app_id} crashed on startup: {raw_error}')

        return port
    except Exception as e:
        hub.logger.error(f'❌ [AppManager] Spawn failed for {app_id}: {e}')
        raise e
