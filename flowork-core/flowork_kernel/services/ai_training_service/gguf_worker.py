########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\ORGINAL\flowork-core\flowork_kernel\services\ai_training_service\gguf_worker.py total lines 171 
########################################################################

import os
import datetime
import traceback
import json
import threading
import shutil
import gc

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
except ImportError:
    pass

UNSLOTH_AVAILABLE = False
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError: pass

class GgufWorker:
    def __init__(self, data_path, models_root, logs_dir):
        self.data_path = data_path
        self.models_root = models_root
        self.logs_dir = logs_dir

    def _log(self, job_id, msg):
        print(f"[{job_id}] {msg}", flush=True)
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_file = os.path.join(self.logs_dir, f"{job_id}.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except: pass

    def run_job(self, job_id, adapter_model_id, quantization, new_model_name, cb, strategy="auto"):
        try:
            cb(job_id, {"status": "PREPARING", "message": f"Analyzing Hardware..."})
            self._execute_smart_gguf(job_id, adapter_model_id, quantization, new_model_name, cb, strategy)
        except Exception as e:
            err_msg = f"GGUF Crash: {str(e)}"
            tb = traceback.format_exc()
            print(f"[GGUF] ERROR job {job_id}: {tb}")
            cb(job_id, {"status": "FAILED", "message": err_msg, "progress": 0})

    def _get_vram_info(self):
        """Intip VRAM GPU yang tersedia"""
        if not torch.cuda.is_available():
            return 0, "CPU Only"

        gpu_name = torch.cuda.get_device_name(0)
        total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3) # GB
        return total_mem, gpu_name

    def _execute_smart_gguf(self, job_id, adapter_model_id, quantization, new_model_name, cb, strategy):
        if not UNSLOTH_AVAILABLE:
            raise ImportError("Unsloth is NOT available. Cannot export to GGUF.")

        self._log(job_id, "--- STARTING SMART GGUF FACTORY ---")

        vram_gb, gpu_name = self._get_vram_info()
        self._log(job_id, f"Hardware: {gpu_name} ({vram_gb:.2f} GB) | Strategy: {strategy}")

        SAFE_THRESHOLD = 18.0

        merge_device = "cuda"

        if strategy == 'cpu':
            merge_device = "cpu"
            self._log(job_id, f"🔧 FORCED CPU MODE: Merging in RAM.")
        elif strategy == 'gpu':
            merge_device = "cuda"
            self._log(job_id, f"🚀 FORCED GPU MODE: Full Speed Ahead.")
        else:
            if vram_gb < SAFE_THRESHOLD:
                merge_device = "cpu"
                self._log(job_id, f"⚠️ VRAM < {SAFE_THRESHOLD}GB. Mode: SMART OFFLOAD (Merge di RAM, Convert di GPU)")
            else:
                self._log(job_id, f"✅ VRAM Sultan! Mode: FULL GPU SPEED")

        if os.path.exists(os.path.join(self.models_root, "text", adapter_model_id)):
             adapter_path = os.path.join(self.models_root, "text", adapter_model_id)
        else:
             adapter_path = adapter_model_id

        if not os.path.exists(adapter_path):
             raise Exception(f"Adapter path not found: {adapter_path}")

        base_model_path = "unsloth/Qwen2.5-7B-bnb-4bit"
        config_file = os.path.join(adapter_path, "adapter_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    conf = json.load(f)
                    base_model_path = conf.get("base_model_name_or_path", base_model_path)
            except: pass

        cb(job_id, {"status": "MERGING", "progress": 10, "message": f"Merging weights ({merge_device})..."})
        self._log(job_id, f"Loading Base Model ({base_model_path}) on {merge_device.upper()}...")

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            device_map=merge_device,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True
        )

        self._log(job_id, "Loading Adapter & Merging...")
        model = PeftModel.from_pretrained(base_model, adapter_path)
        model = model.merge_and_unload()

        output_dir = os.path.join(self.models_root, "gguf")
        if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)

        safe_name = "".join([c for c in new_model_name if c.isalpha() or c.isdigit() or c in ('-','_')]).strip()
        temp_merge_dir = os.path.join(output_dir, f"temp_smart_{safe_name}")

        if os.path.exists(temp_merge_dir): shutil.rmtree(temp_merge_dir)
        os.makedirs(temp_merge_dir, exist_ok=True)

        self._log(job_id, f"Saving merged model to temp storage: {temp_merge_dir}")
        cb(job_id, {"progress": 30, "message": "Saving merged weights..."})

        model.save_pretrained(temp_merge_dir)
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        tokenizer.save_pretrained(temp_merge_dir)

        self._log(job_id, "Cleaning up memory for conversion phase...")
        del model
        del base_model
        gc.collect()
        torch.cuda.empty_cache()

        self._log(job_id, "Starting GGUF Quantization Phase...")
        cb(job_id, {"progress": 50, "message": f"Quantizing to {quantization}..."})

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name = temp_merge_dir,
            max_seq_length = 2048,
            dtype = None,
            load_in_4bit = False,
        )

        model.save_pretrained_gguf(
            temp_merge_dir,
            tokenizer,
            quantization_method = quantization
        )

        self._log(job_id, "Organizing output files...")
        generated_files = [f for f in os.listdir(temp_merge_dir) if f.endswith(".gguf")]
        final_path = ""

        if generated_files:
            src = os.path.join(temp_merge_dir, generated_files[0])
            dst = os.path.join(output_dir, f"{new_model_name}.gguf")
            if os.path.exists(dst): os.remove(dst)
            shutil.move(src, dst)
            final_path = dst
            try: shutil.rmtree(temp_merge_dir)
            except: pass

        self._log(job_id, f"✅ SMART GGUF SUCCESS! Saved at: {final_path}")
        cb(job_id, {"status": "COMPLETED", "message": "GGUF Conversion Success!", "progress": 100})
