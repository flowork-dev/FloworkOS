########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\modules\prompt_receiver_module\processor.py total lines 102 
########################################################################

import sys
import json
import traceback
from flowork_kernel.api_contract import BaseModule, IExecutable

class PromptReceiver(BaseModule, IExecutable):

    TIER = "architect"

    def __init__(self, module_id, services):
        super().__init__(module_id, services)
        self.kernel = services.get("kernel")
        self.ai_service = services.get("ai_architect_service")

    def execute(self, payload: dict, config: dict, status_updater, mode="EXECUTE", **kwargs):
        """
        Fungsi utama yang dipanggil saat module dijalankan.
        SPY MODE: ACTIVE - Lapor semua pergerakan data!
        """
        if mode == "SIMULATE":
            return {"payload": {"data": payload}, "output_name": "success"}

        try:
            print(f"\n[SPY-RECEIVER] 🕵️‍♂️ === START INSPECTION ===", file=sys.stderr)
            print(f"[SPY-RECEIVER] 📦 Incoming Keys: {list(payload.keys())}", file=sys.stderr)
            print(f"[SPY-RECEIVER] 📄 Full Payload: {json.dumps(payload, default=str)}", file=sys.stderr)


            user_prompt = None
            source = "unknown"
            debug_info = []

            if "prompt" in payload:
                user_prompt = payload.get("prompt")
                source = "payload (root)"
                debug_info.append("✅ Found in Root")

            elif "global_payload" in payload:
                nested = payload.get("global_payload", {})
                if isinstance(nested, dict) and "prompt" in nested:
                    user_prompt = nested.get("prompt")
                    source = "payload.global_payload (AUTO-FIX)"
                    debug_info.append("🔧 Extracted from global_payload")

            elif "initial_payload" in payload:
                nested = payload.get("initial_payload", {})
                if isinstance(nested, dict) and "prompt" in nested:
                    user_prompt = nested.get("prompt")
                    source = "payload.initial_payload (AUTO-FIX)"
                    debug_info.append("🔧 Extracted from initial_payload")

            if not user_prompt:
                user_prompt = config.get("prompt")
                if user_prompt:
                    source = "config (properties)"
                    debug_info.append("⚠️ Using Config Fallback")

            final_prompt = str(user_prompt).strip() if user_prompt else ""

            status_msg = f"📩 Spy Report: Dapet dari {source} | Keys: {list(payload.keys())}"

            status_updater(status_msg, "INFO")
            print(f"[SPY-RECEIVER] 🔍 Detection Result: {status_msg}", file=sys.stderr)

            if not final_prompt:
                err_details = f"Prompt KOSONG! Spy bingung. Cek log 'Incoming Keys' diatas."
                print(f"[SPY-RECEIVER] ❌ {err_details}", file=sys.stderr)
                return self._error(err_details, status_updater)

            print(f"[SPY-RECEIVER] ✅ ACCEPTED PROMPT: {final_prompt[:100]}...", file=sys.stderr)
            print(f"[SPY-RECEIVER] 🕵️‍♂️ === END INSPECTION ===\n", file=sys.stderr)

            output_data = {
                "original_prompt": final_prompt,
                "status": "received",
                "source": source,
                "spy_report": debug_info, # Kirim laporan mata-mata ke output node berikutnya
                "message": "Pesan berhasil ditangkap oleh Spy Receiver!"
            }

            status_updater(f"✅ Misi Sukses! Data: {source}", "SUCCESS")

            return {
                "payload": {
                    "data": output_data
                },
                "output_name": "success"
            }

        except Exception as e:
            traceback.print_exc()
            return self._error(f"Spy Error: {str(e)}", status_updater)

    def _error(self, msg, updater):
        updater(msg, "ERROR")
        return {"payload": {"data": {"error": msg}}, "output_name": "error"}
