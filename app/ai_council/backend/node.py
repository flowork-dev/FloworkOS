########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\backend\node.py total lines 121 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import shutil
import subprocess
import logging
import time

try:
    from flowork_kernel.flow_sdk.base_app_node import BaseAppNode
except ImportError:
    class BaseAppNode:
        def __init__(self): pass

logger = logging.getLogger("Node.ai_council")

class DependencyLazarus:
    """
    ⚔️ THE LAZARUS PROTOCOL
    Tugas: Mendeteksi library busuk, membakarnya (delete), dan menghidupkannya kembali (reinstall).
    """
    LIB_PATH = "/app/data/global_libs"

    @staticmethod
    def _nuke_library(package_name):
        """Hapus folder library sampai ke akar-akarnya."""
        target_dir = os.path.join(DependencyLazarus.LIB_PATH, package_name)
        if os.path.exists(target_dir):
            logger.warning(f"☢️ [Lazarus] Nuking corrupt library: {package_name}...")
            try:
                shutil.rmtree(target_path)
                logger.info(f"✅ [Lazarus] {package_name} has been purged.")
            except Exception as e:
                logger.error(f"❌ [Lazarus] Failed to nuke {package_name}: {e}")

    @staticmethod
    def _resurrect_library(package_name, install_name=None):
        """Install ulang library."""
        real_name = install_name or package_name
        logger.info(f"🧬 [Lazarus] Resurrecting (Installing): {real_name}...")
        try:
            cmd = [
                sys.executable, "-m", "pip", "install",
                real_name,
                "--target", DependencyLazarus.LIB_PATH,
                "--no-cache-dir",
                "--upgrade",
                "--force-reinstall"
            ]
            subprocess.check_call(cmd)
            logger.info(f"✅ [Lazarus] {real_name} is ALIVE!")
        except Exception as e:
            logger.error(f"❌ [Lazarus] Resurrection failed for {real_name}: {e}")

    @staticmethod
    def ensure_torch():
        try:
            import torch
            logger.info(f"✅ [Check] Torch Version: {torch.__version__}")
        except (ImportError, ModuleNotFoundError, OSError) as e:
            logger.error(f"💀 [Check] Torch is dead/corrupt: {e}")
            DependencyLazarus._nuke_library("torch")
            DependencyLazarus._resurrect_library("torch")

    @staticmethod
    def ensure_genai():
        try:
            import google.genai
            logger.info("✅ [Check] Google GenAI is ready.")
        except (ImportError, ModuleNotFoundError) as e:
            logger.error(f"💀 [Check] Google GenAI missing: {e}")
            DependencyLazarus._resurrect_library("google", "google-genai")

class AICouncilNode(BaseAppNode):
    def __init__(self):
        super().__init__()
        self.client = None
        self.model_name = "gemini-2.0-flash-exp"

        logger.info("🛡️ [System] Initiating Lazarus Integrity Check...")
        DependencyLazarus.ensure_genai()

    def _setup_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("❌ [AI Council] GEMINI_API_KEY Missing!")
            return False

        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
            logger.info("✅ [AI Council] Gemini Client Connected.")
            return True
        except ImportError:
            logger.error("❌ [AI Council] GenAI Library still missing after Lazarus!")
            return False

    def run(self, payload):
        action = payload.get("action", "unknown")

        if not self.client:
            if not self._setup_gemini():
                return {"status": "error", "message": "Dependensi Kritis Hilang. Cek Log Server."}

        try:
            prompt = payload.get("prompt")
            if prompt:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return {"status": "success", "response": response.text}
            return {"status": "success", "message": "System Ready."}

        except Exception as e:
            return {"status": "error", "message": str(e)}
