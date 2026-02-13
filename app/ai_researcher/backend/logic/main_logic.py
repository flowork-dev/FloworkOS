########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_researcher\backend\logic\main_logic.py total lines 95 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import json
import os
import sys

def run(app_context, data, *args, **kwargs):
    """
    Logic AI Analysis (Modern Standard v1.x) dengan Neural Path Injector.
    Menggabungkan kemampuan deteksi library otomatis dan syntax OpenAI terbaru.
    """

    try:
        global_lib_path = "/app/data/global_libs"
        if os.path.exists(global_lib_path):
            for lib_name in os.listdir(global_lib_path):
                lib_dir = os.path.join(global_lib_path, lib_name)
                if os.path.isdir(lib_dir):
                    for ver_hash in os.listdir(lib_dir):
                        full_path = os.path.join(lib_dir, ver_hash)
                        if full_path not in sys.path:
                            sys.path.append(full_path)
    except Exception as e:
        pass

    try:
        from openai import OpenAI
    except ImportError:
        try:
            import openai
            version = getattr(openai, "__version__", "unknown")
            return {
                "status": "error",
                "message": f"Library conflict: Terdeteksi OpenAI v{version}, tapi butuh v1.x (Class 'OpenAI' tidak ditemukan). Cek requirements.txt."
            }
        except:
            return {
                "status": "error",
                "message": "Library 'openai' lenyap. Pastikan requirements.txt berisi 'openai>=1.0.0' dan restart app."
            }

    try:

        var_manager = app_context.kernel.get_service("variable_manager")
        api_key = var_manager.get_variable("OPENAI_API_KEY")

        if not api_key:
            return {"status": "error", "message": "OPENAI_API_KEY missing in Config."}

        client = OpenAI(api_key=api_key)

        text_to_analyze = data.get('text', '')
        if not text_to_analyze:
            return {"status": "failure", "message": "No text provided to analyze."}

        system_prompt = (
            "You are a strategic analyst. Analyze the text provided. "
            "Return output in strict JSON format with keys: "
            "'summary', 'strategic_risks', 'action_items'. "
            "Do not use markdown blocks."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_to_analyze}
            ]
        )

        raw_content = response.choices[0].message.content

        clean_content = raw_content.replace("```json", "").replace("```", "").strip()

        try:
            parsed_data = json.loads(clean_content)
        except json.JSONDecodeError:
            parsed_data = {
                "summary": raw_content,
                "strategic_risks": "Check raw output",
                "action_items": "Check raw output"
            }

        return {
            "status": "success",
            "data": parsed_data,
            "message": "Analysis complete."
        }

    except Exception as e:
        return {"status": "error", "message": f"Logic Error: {str(e)}"}
