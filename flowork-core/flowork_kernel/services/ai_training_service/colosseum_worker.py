########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_training_service\colosseum_worker.py total lines 126 
########################################################################

import traceback
import time
import gc
import threading

try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
    from peft import PeftModel
except ImportError:
    pass

class ColosseumWorker:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.active_base_id = None
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def _unload_model(self):
        """Bersihin VRAM sampai kinclong"""
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        self.active_base_id = None

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[Colosseum] VRAM flushed. Ring cleared.")

    def _load_base_if_needed(self, base_path, base_id):
        """Cek apakah model base udah standby, kalau belum, load baru."""
        if self.active_base_id == base_id and self.model is not None:
            print(f"[Colosseum] Base Model '{base_id}' already warm in VRAM. Skipping load.")
            return # UDAH READY BRO!

        print(f"[Colosseum] Loading Base Model: {base_id}...")
        self._unload_model() # Buang yang lama

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(base_path)

            self.model = AutoModelForCausalLM.from_pretrained(
                base_path,
                device_map="auto",
                load_in_4bit=True, # FITUR HEMAT MEMORI
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            self.active_base_id = base_id
            print(f"[Colosseum] Base Model '{base_id}' loaded successfully!")

        except Exception as e:
            print(f"[Colosseum] Failed to load base model: {e}")
            self._unload_model()
            raise e

    def run_sparring_match(self, base_model_path, adapter_path, prompt, base_name, adapter_name):
        with self._lock:
            print(f"[Colosseum] ⚔️ SPARRING START: {base_name} vs {adapter_name}")

            try:
                if not torch.cuda.is_available():
                    time.sleep(1)
                    return {
                        "base_reply": f"[CPU MOCK] Base Model ({base_name}) says: I assume '{prompt}' is interesting.",
                        "adapter_reply": f"[CPU MOCK] Adapter ({adapter_name}) says: Based on my training, '{prompt}' is crucial!"
                    }

                self._load_base_if_needed(base_model_path, base_name)

                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

                print("[Colosseum] Round 1: Base Model Inference...")
                with torch.no_grad():
                    outputs_base = self.model.generate(
                        **inputs,
                        max_new_tokens=256,
                        do_sample=True,
                        temperature=0.7
                    )
                base_text = self.tokenizer.decode(outputs_base[0], skip_special_tokens=True)
                base_text = base_text.replace(prompt, "").strip()

                print(f"[Colosseum] Round 2: Attaching Adapter {adapter_name}...")

                peft_model = PeftModel.from_pretrained(self.model, adapter_path)

                print("[Colosseum] Fighting with Adapter...")
                with torch.no_grad():
                    outputs_adapter = peft_model.generate(
                        **inputs,
                        max_new_tokens=256,
                        do_sample=True,
                        temperature=0.7
                    )
                adapter_text = self.tokenizer.decode(outputs_adapter[0], skip_special_tokens=True)
                adapter_text = adapter_text.replace(prompt, "").strip()

                print("[Colosseum] Detaching Adapter to save state...")
                self.model = peft_model.unload()

                del peft_model

                return {
                    "base_reply": base_text,
                    "adapter_reply": adapter_text
                }

            except Exception as e:
                traceback.print_exc()
                return {"error": f"Sparring Error: {str(e)}"}
