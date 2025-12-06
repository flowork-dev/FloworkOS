########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_training_service\training_worker.py total lines 234 
########################################################################

UNSLOTH_AVAILABLE = False
try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True

    try:
        import unsloth_zoo.fused_losses.cross_entropy_loss
        original_get_multiplier = unsloth_zoo.fused_losses.cross_entropy_loss._get_chunk_multiplier

        def safe_get_chunk_multiplier(vocab_size, target_gb):
            if target_gb is None or target_gb <= 0:
                print(f"[TrainingWorker] ⚠️ WARNING: Detected target_gb={target_gb}. Forcing 0.5GB to prevent crash.")
                target_gb = 0.5
            return original_get_multiplier(vocab_size, target_gb)

        unsloth_zoo.fused_losses.cross_entropy_loss._get_chunk_multiplier = safe_get_chunk_multiplier
        print("[TrainingWorker] 🛡️ Unsloth ZeroDivisionError Patch APPLIED.")
    except Exception as e:
        print(f"[TrainingWorker] ⚠️ Failed to apply Unsloth Patch: {e}")

except ImportError:
    pass

import os
import datetime
import traceback
import json
import threading
import gc
import shutil # [NEW] Added for directory cleanup

try:
    import torch
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments,
        DataCollatorForLanguageModeling, TrainerCallback, BitsAndBytesConfig
    )
    from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
    from trl import SFTTrainer
except ImportError:
    pass

class TrainingWorker:
    def __init__(self, data_path, models_root, logs_dir):
        self.data_path = data_path
        self.models_root = models_root
        self.logs_dir = logs_dir

    def run_job(self, job_id, model_path, dataset_name, new_model_name, args, dataset_data, status_callback):
        try:
            status_callback(job_id, {"status": "PREPARING", "message": "Initializing Dynamic Training..."})
            self._run_heavy_training(job_id, model_path, dataset_name, new_model_name, args, dataset_data, status_callback)
        except Exception as e:
            err_msg = f"Worker Crash: {str(e)}"
            tb = traceback.format_exc()
            print(f"[Training] CRITICAL ERROR job {job_id}: {tb}")
            status_callback(job_id, {"status": "FAILED", "message": err_msg, "progress": 0})

    def _log(self, job_id, msg):
        print(f"[{job_id}] {msg}", flush=True)
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_file = os.path.join(self.logs_dir, f"{job_id}.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {msg}\n")
        except: pass

    def _run_heavy_training(self, job_id, base_model_path, dataset_name, new_model_name, training_args, dataset_data, cb):
        self._log(job_id, f"--- STARTING TRAINING JOB {job_id} ---")

        try:
            torch.cuda.empty_cache()
            gc.collect()
        except: pass

        use_cuda = torch.cuda.is_available()

        from datasets import Dataset
        formatted_data = []
        for item in dataset_data:
            p = str(item.get('prompt', '')).strip()
            r = str(item.get('response', '')).strip()

            t = str(item.get('text', '')).strip()

            if p and r:
                text = f"<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n{r}<|im_end|>"
                formatted_data.append({"text": text})
            elif t:
                formatted_data.append({"text": t})

        hf_dataset = Dataset.from_list(formatted_data)
        self._log(job_id, f"Dataset loaded: {len(formatted_data)} samples.")

        if len(formatted_data) == 0:
            raise ValueError("Dataset is empty! Check if your source file has text content.")

        output_dir = os.path.join(self.models_root, "text", new_model_name)

        MAX_SEQ_LENGTH = int(training_args.get("max_seq_length", 2048))
        LORA_RANK = int(training_args.get("lora_rank", 16))

        BATCH_SIZE = int(training_args.get("batch_size", 1))
        GRAD_ACC = int(training_args.get("gradient_accumulation_steps", 4))
        EPOCHS = int(training_args.get("epochs", 1))

        self._log(job_id, f"Config: Ctx={MAX_SEQ_LENGTH} | Rank={LORA_RANK} | Batch={BATCH_SIZE} | Grad={GRAD_ACC}")

        cb(job_id, {"status": "PREPARING", "message": f"Loading Model (Ctx: {MAX_SEQ_LENGTH})...", "progress": 5})

        model = None
        tokenizer = None

        if UNSLOTH_AVAILABLE and use_cuda:
            self._log(job_id, "⚡ ACTIVATING UNSLOTH (DYNAMIC MODE) ⚡")
            try:
                model, tokenizer = FastLanguageModel.from_pretrained(
                    model_name = base_model_path,
                    max_seq_length = MAX_SEQ_LENGTH,
                    dtype = None,
                    load_in_4bit = True,
                    device_map = {"": 0}, # Force Single GPU
                    gpu_memory_utilization = 0.90,
                )

                model = FastLanguageModel.get_peft_model(
                    model,
                    r = LORA_RANK,
                    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                    lora_alpha = LORA_RANK,
                    lora_dropout = 0,
                    bias = "none",
                    use_gradient_checkpointing = "unsloth",
                    random_state = 3407,
                    use_rslora = True,
                    loftq_config = None,
                )
            except Exception as e:
                self._log(job_id, f"Unsloth init failed: {e}")
                model = None

        if model is None:
            self._log(job_id, "⚠️ Fallback to Standard Transformers.")
            try:
                tokenizer = AutoTokenizer.from_pretrained(base_model_path)
                if tokenizer.pad_token is None: tokenizer.pad_token = tokenizer.eos_token
                model = AutoModelForCausalLM.from_pretrained(base_model_path, device_map="auto")
                config = LoraConfig(r=LORA_RANK, lora_alpha=LORA_RANK, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM")
                model = get_peft_model(model, config)
            except Exception as e:
                raise e

        t_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACC,
            warmup_steps=5,
            max_steps=-1,
            learning_rate=2e-4,
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_dir=self.logs_dir,
            report_to="none",
            save_total_limit=2, # [NEW] Only keep last 2 checkpoints during run
        )

        worker_ref = self
        class ActiveLogCallback(TrainerCallback):
            def on_log(self, args, state, control, logs=None, **kwargs):
                if logs and "loss" in logs:
                    worker_ref._log(job_id, f"[TRAIN] Step {state.global_step} | Loss: {logs['loss']:.4f}")

        self._log(job_id, f">>> STARTING TRAINING <<<")

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=hf_dataset,
            dataset_text_field="text",
            max_seq_length=MAX_SEQ_LENGTH,
            dataset_num_proc=2,
            packing=False,
            args=t_args,
            callbacks=[ActiveLogCallback()]
        )

        cb(job_id, {"status": "TRAINING", "message": "Training in progress...", "progress": 10})

        trainer.train()

        cb(job_id, {"message": "Saving optimized adapter...", "progress": 90})
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        config_path = os.path.join(output_dir, "adapter_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f: conf = json.load(f)
                conf['base_model_name_or_path'] = base_model_path
                with open(config_path, "w") as f: json.dump(conf, f, indent=4)
            except: pass

        self._log(job_id, "🧹 Cleaning up temporary checkpoints...")
        try:
            for item in os.listdir(output_dir):
                if item.startswith("checkpoint-"):
                    chk_path = os.path.join(output_dir, item)
                    if os.path.isdir(chk_path):
                        shutil.rmtree(chk_path)
            self._log(job_id, "✨ Disk cache clean. Only final model preserved.")
        except Exception as e:
            self._log(job_id, f"⚠️ Disk cleanup warning: {e}")

        cb(job_id, {"status": "COMPLETED", "message": "Training Selesai!", "progress": 100})

        try:
            import gc
            del model
            del tokenizer
            gc.collect()
            torch.cuda.empty_cache()
        except: pass
