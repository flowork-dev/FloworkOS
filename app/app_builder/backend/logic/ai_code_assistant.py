########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\app_builder\backend\logic\ai_code_assistant.py total lines 293 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import json
import re
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # /app/backend
RULES_DIR = os.path.join(BASE_DIR, "rules")
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
LOG_FILE = os.path.join(MEMORY_DIR, "evolution_logs.json")

os.makedirs(MEMORY_DIR, exist_ok=True)

FALLBACK_RULES = {
    "main_logic_py": "Use standard Python. Def run(app_context, data, *args, **kwargs). Return dict status.",
    "index_html": "Full functional HTML/JS. No placeholders. Use Tailwind CSS.",
    "manifest": "Valid JSON manifest with 'id', 'entry_point', 'permissions'.",
    "config_schema": "Valid JSON schema with 'variables' list."
}


def get_rule_content(step_name):
    """Load Rule from File OR Fallback"""
    step_map = {
        "main_logic_py": "main_logic.md",
        "index_html": "index_html.md",
        "manifest": "manifest.md",
        "config_schema": "config_schema.md",
        "requirements_txt": "requirements.md",
        "app_service_py": "app_service.md",
        "app_router_py": "app_router.py.md",
        "icon_svg": "icon.md"
    }

    rule_file = step_map.get(step_name, "general_python.md")
    rule_path = os.path.join(RULES_DIR, rule_file)

    if os.path.exists(rule_path):
        return f"\n\n--- RULE FILE: {os.path.basename(rule_path)} ---\n" + open(rule_path, "r", encoding="utf-8").read()

    fallback = FALLBACK_RULES.get(step_name, "FOLLOW STANDARD CODING PRACTICES.")
    return f"\n\n--- EMERGENCY RULE (FILE MISSING) ---\n{fallback}"

def get_evolution_memory(step_name):
    """Baca sejarah kesalahan"""
    if not os.path.exists(LOG_FILE): return ""
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
            step_logs = logs.get(step_name, [])
            if not step_logs: return ""
            seen = set()
            unique_logs = []
            for log in step_logs:
                if log['error'] not in seen:
                    unique_logs.append(log)
                    seen.add(log['error'])

            memory_text = "\n\n!!! PREVIOUS MISTAKES (DO NOT REPEAT) !!!\n"
            for log in unique_logs[-3:]:
                memory_text += f"- VIOLATION: {log['error']}\n"
            return memory_text
    except: return ""

def record_mistake(step_name, error_msg):
    """Rekam dosa (Anti-Duplicate & Auto-Pruning)"""
    logs = {}
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f: logs = json.load(f)
    except: pass

    if step_name not in logs: logs[step_name] = []

    existing_errors = [entry.get('error') for entry in logs[step_name]]

    if error_msg not in existing_errors:
        logs[step_name].append({
            "timestamp": str(datetime.now()),
            "error": error_msg
        })

        if len(logs[step_name]) > 50:
             logs[step_name] = logs[step_name][-50:]

        try:
            with open(LOG_FILE, 'w') as f: json.dump(logs, f, indent=2)
        except: pass

def extract_content(text, step_name):
    """
    V14 SEPARATOR ENGINE:
    Membedakan cara ekstraksi JSON vs Code.
    """
    text = text.strip()

    if step_name in ["manifest", "config_schema"]:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))

                if step_name == "manifest":
                    if "config" in data or "variables" in data:
                        return None, "MANIFEST_POLLUTED (Jangan masukkan config/variables ke sini!)"
                    if "id" not in data or "entry_point" not in data:
                        return None, "INVALID_MANIFEST (Missing 'id' or 'entry_point')"

                if step_name == "config_schema":
                    if "entry_point" in data or "permissions" in data:
                        return None, "CONFIG_POLLUTED (Jangan masukkan metadata Manifest ke sini!)"
                    if "variables" not in data:
                        return None, "INVALID_CONFIG (Must contain 'variables' array)"

                return data, None
            except json.JSONDecodeError:
                return None, "INVALID_JSON_FORMAT"
        return None, "NO_JSON_FOUND"

    else:
        code_match = re.search(r"```(?:\w+)?\s*(.*?)\s*```", text, re.DOTALL)
        if code_match:
            return code_match.group(1), None

        if "Here is the code" not in text and len(text) > 20:
             return text, None

        return None, "NO_CODE_BLOCK_FOUND"


def run(context, data, *args, **kwargs):
    """
    EVOLUTION BRAIN V14.6 (Smart Filter):
    - Fix FALSE POSITIVE pada filter "placeholder" untuk file HTML.
    - Mencegah Retry Loop yang menyebabkan Gateway Timeout.
    """
    prompt = data.get('prompt', '').strip()
    target_model = data.get('model', 'gpt-4o')
    app_id = data.get('app_id', 'new_evolution_app')
    current_step = data.get('step', 'main_logic_py')
    user_id = data.get('user_id')
    logger = logging.getLogger("AppRouter.Evolution_Architect")

    NEURAL_INJECTOR_CODE = """
    import sys, os
    try:
        global_lib_path = "/app/data/global_libs"
        if os.path.exists(global_lib_path):
            for lib_name in os.listdir(global_lib_path):
                lib_dir = os.path.join(global_lib_path, lib_name)
                if os.path.isdir(lib_dir):
                    for ver_hash in os.listdir(lib_dir):
                        sys.path.append(os.path.join(lib_dir, ver_hash))
    except: pass
    """

    try:
        kernel = context.kernel
        app_service = kernel.get_service('app_service')
        ai_service = kernel.get_service('ai_provider_manager_service')

        app_path = os.path.join(app_service.base_app_path, app_id)
        memory_context = ""

        if os.path.exists(app_path):
            priority_files = []
            if current_step == "main_logic_py":
                priority_files = ["manifest.json", "config_schema.json"]
            elif current_step == "index_html":
                priority_files = ["manifest.json", "main_logic.py"]
            elif current_step == "app_router_py":
                priority_files = ["manifest.json", "app_service.py"]
            elif current_step == "manifest":
                priority_files = ["config_schema.json"]
            else:
                priority_files = ["manifest.json", "main_logic.py"]

            for fname in priority_files:
                fpath = os.path.join(app_path, fname)
                if os.path.exists(fpath):
                    with open(fpath, "r", encoding="utf-8") as f:
                        memory_context += f"\nFILE: {fname}\nCONTENT:\n{f.read()[:1500]}\n"

        combined_rules = get_rule_content(current_step)
        evolution_memory = get_evolution_memory(current_step)

        if current_step in ["manifest", "config_schema"]:
            format_instruction = (
                "OUTPUT FORMAT: Return ONLY valid JSON object.\n"
                "DO NOT wrap in 'app_bundle'. Return the root object directly.\n"
                "STRICTLY FOLLOW THE SCHEMA DEFINED IN THE RULE."
            )
        else:
            format_instruction = (
                "OUTPUT FORMAT: Return ONLY the RAW CODE enclosed in Markdown ``` code block.\n"
                "Ensure imports are correct."
            )

        base_prompt = (
            f"!!! SYSTEM OVERRIDE: YOU ARE A STRICT CODE GENERATOR !!!\n"
            f"TASK: Generate content for file '{current_step}' ONLY.\n"
            f"APP_ID: '{app_id}'\n"
            f"{combined_rules}\n"
            f"{evolution_memory}\n"
            f"CONTEXT FILES (Relevant Only):\n{memory_context}\n"
            f"USER REQUEST: {prompt}\n"
            f"--------------------------------------------------\n"
            f"{format_instruction}\n"
            f"WARNING: Focus ONLY on {current_step}. Do not hallucinate content from other files."
        )

        attempts = 0
        max_attempts = 4
        last_error = ""
        current_ai_prompt = base_prompt

        while attempts < max_attempts:
            attempts += 1
            logger.info(f"🧠 Architect V14.6 thinking... ({attempts}/{max_attempts}) for {current_step}")

            if hasattr(ai_service, 'run'):
                response = ai_service.run({"action": "generate", "prompt": current_ai_prompt, "user_id": user_id, "model": target_model})
                raw_res = response.get('data') or response.get('response') or str(response)
            else:
                response = ai_service.generate_text(prompt=current_ai_prompt, model=target_model, user_id=user_id)
                raw_res = response.get('content') or str(response)

            content, error = extract_content(raw_res, current_step)

            if content is not None:
                if current_step == "main_logic_py" and isinstance(content, str):
                    if "def run" in content and "global_lib_path" not in content:
                        if "def run" in content:
                            parts = content.split("def run", 1)
                            content = parts[0] + NEURAL_INJECTOR_CODE + "\ndef run" + parts[1]
                        else:
                            content = NEURAL_INJECTOR_CODE + "\n" + content

                val_str = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
                val_lower = val_str.lower()
                violations = []

                if current_step == "index_html":
                    forbidden_words = ["dummy data", "coming soon", "lorem ipsum", "logic goes here"]
                else:
                    forbidden_words = ["placeholder", "dummy data", "coming soon", "lorem ipsum"]

                found_bad_words = [word for word in forbidden_words if word in val_lower]

                if current_step not in ["config_schema", "manifest"]:
                    if found_bad_words:
                        violations.append(f"DUMMY_DETECTED ({', '.join(found_bad_words)})")

                if current_step == "main_logic_py":
                    if "flask" in val_lower or "@app.route" in val_lower:
                        violations.append("FLASK_DETECTED")
                    if "os.environ" in val_str or "os.getenv" in val_str:
                         violations.append("SECURITY_RISK (os.getenv)")

                min_len = 20
                if len(val_str.strip()) < min_len:
                    violations.append("TOO_SHORT")

                if violations:
                    last_error = ", ".join(violations)
                    record_mistake(current_step, last_error)
                else:
                    final_bundle = {current_step: content}
                    return {"status": "success", "app_bundle": final_bundle}

            else:
                last_error = error or "EXTRACTION_FAILED"

            current_ai_prompt = (
                f"{base_prompt}\n\n"
                f"--- REJECTION NOTICE (Attempt {attempts}) ---\n"
                f"ERROR: {last_error}\n"
                f"INSTRUCTION: REWRITE the content. Fix the error above.\n"
                f"Ensure you return ONLY the content for {current_step}.\n"
                f"DO NOT mix Manifest and Config logic!"
            )
            logger.warning(f"Architect V14.6 rejection: {last_error}")

        return {"status": "error", "message": f"ARCHITECT_FAILED: {last_error}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
