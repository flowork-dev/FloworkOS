########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\neural_dojo\backend\app_service.py total lines 222 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import os
import sys
import threading
import json
import time
import logging
import torch
from pathlib import Path
from datetime import datetime
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    TrainerCallback
)
from datasets import load_dataset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FloworkLogCallback(TrainerCallback):
    def __init__(self, service):
        self.service = service

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            loss = logs.get("loss", None)
            epoch = logs.get("epoch", 0)
            if loss:
                with self.service.state_lock:
                    self.service.state["current_loss"] = round(float(loss), 4)
                    self.service.state["loss_history"].append(float(loss))
                    self.service.state["current_epoch"] = epoch
                self.service.log(f"📉 Training Step - Loss: {loss:.4f}", "info")

class NeuralService:
    def __init__(self, kernel, service_id):
        self.kernel = kernel
        self.service_id = service_id
        self.logger = logging.getLogger(f"Service.{service_id}")
        self.stop_event = threading.Event()

        self.base_dir = self._get_base_dir()

        self.models_dir = self.base_dir / "models_cache"
        self.datasets_dir = self.base_dir / "datasets_cache"

        self._ensure_directories()

        self.state = {
            "is_training": False, "current_epoch": 0, "total_epochs": 0,
            "current_loss": 0.0, "loss_history": [], "logs": [],
            "model_name": "None", "status": "idle"
        }
        self.state_lock = threading.Lock()
        self.log(f"✅ Neural Engine Online. Storage Root: {self.base_dir}", "system")

    def _get_base_dir(self):
        """
        Logika Pintar untuk menentukan lokasi data.
        Prioritas: /app/data (Mapping Docker dari C:\FLOWORK\data)
        """
        docker_path = Path("/app/data")
        if docker_path.exists():
            return docker_path

        win_path = Path(r"C:\FLOWORK\data")
        if win_path.exists():
            return win_path

        return Path(os.getcwd()) / "data"

    def _ensure_directories(self):
        for d in [self.models_dir, self.datasets_dir]:
            if not d.exists():
                try:
                    d.mkdir(parents=True, exist_ok=True)
                    self.log(f"📂 Created directory: {d}", "system")
                except Exception as e:
                    self.log(f"⚠️ Failed create dir {d}: {e}", "warning")

    def log(self, message, level="info"):
        entry = {"time": datetime.now().strftime("%H:%M:%S"), "message": message, "level": level}
        with self.state_lock:
            self.state["logs"].append(entry)
            if len(self.state["logs"]) > 100: self.state["logs"].pop(0)
        self.logger.info(f"[{level.upper()}] {message}")


    def get_status(self):
        with self.state_lock: return json.loads(json.dumps(self.state))

    def scan_local_models(self):
        models = []
        if self.models_dir.exists():
            for item in self.models_dir.iterdir():
                if item.is_dir(): models.append(item.name)
        return {"status": "success", "models": models}

    def list_directory(self, path, user_id="system"):
        if not path or path.strip() == "":
            target_path = self.base_dir
        else:
            target_path = Path(path)

        if not target_path.exists():
            target_path = self.base_dir

        items = []
        try:
            for item in target_path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "folder" if item.is_dir() else "file",
                    "path": str(item).replace("\\", "/")
                })
            items.sort(key=lambda x: (x["type"] != "folder", x["name"].lower()))

            return {
                "status": "success",
                "data": items,
                "current_path": str(target_path).replace("\\", "/")
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "current_path": str(self.base_dir)}

    def stop_training(self):
        if not self.state["is_training"]: return {"status": "warning", "message": "Idle"}
        self.stop_event.set()
        self.log("🛑 Stopping...", "system")
        return {"status": "success"}

    def start_training(self, config):
        if self.state["is_training"]: return {"status": "error", "message": "Busy"}
        self.stop_event.clear()
        thread = threading.Thread(target=self._run_real_training, args=(config,))
        thread.daemon = True
        thread.start()
        return {"status": "success"}

    def _run_real_training(self, config):
        model_name = config.get("model_name", "bert-base-uncased")
        dataset_path = config.get("dataset_path", "")
        epochs = int(config.get("epochs", 3))
        lr = float(config.get("learning_rate", 2e-5))

        with self.state_lock:
            self.state.update({"is_training": True, "status": "preparing", "total_epochs": epochs})

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.log(f"🔥 Hardware: {device.upper()}", "system")

            if not dataset_path: raise Exception("No Dataset Path")

            d_path = Path(dataset_path)
            if d_path.is_file():
                files = [str(d_path)]
            else:
                files = [str(f) for f in d_path.glob("*.json")]

            if not files: raise Exception(f"No .json files in {dataset_path}")

            dataset = load_dataset("json", data_files=files, split="train")
            self.log(f"📊 Dataset: {len(dataset)} items", "success")

            local_model_path = self.models_dir / model_name
            load_path = str(local_model_path) if local_model_path.exists() else model_name

            tokenizer = AutoTokenizer.from_pretrained(load_path)
            model = AutoModelForCausalLM.from_pretrained(load_path).to(device)
            if not tokenizer.pad_token: tokenizer.pad_token = tokenizer.eos_token

            def preprocess(examples):
                inputs = [f"Instruct: {i}\nInput: {inpt}\nOutput: " for i, inpt in zip(examples["instruction"], examples["input"])]
                targets = examples["output"]
                model_inputs = tokenizer(inputs, max_length=128, truncation=True, padding="max_length")
                labels = tokenizer(targets, max_length=128, truncation=True, padding="max_length")
                model_inputs["labels"] = labels["input_ids"]
                return model_inputs

            tokenized = dataset.map(preprocess, batched=True)

            output_dir = self.models_dir / f"{model_name}_finetuned_{int(time.time())}"

            args = TrainingArguments(
                output_dir=str(output_dir),
                num_train_epochs=epochs,
                per_device_train_batch_size=1,
                learning_rate=lr,
                logging_steps=1,
                save_steps=500,
                report_to="none",
                use_cpu=(device == "cpu")
            )

            with self.state_lock: self.state["status"] = "training"
            trainer = Trainer(
                model=model, args=args, train_dataset=tokenized,
                data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
                callbacks=[FloworkLogCallback(self)]
            )

            trainer.train()
            trainer.save_model()
            self.log(f"🏆 Training Done! Saved to {output_dir.name}", "success")
            with self.state_lock: self.state["status"] = "completed"

        except Exception as e:
            self.log(f"❌ Error: {str(e)}", "error")
            import traceback
            traceback.print_exc()
            with self.state_lock: self.state["status"] = "error"
        finally:
            with self.state_lock: self.state["is_training"] = False
