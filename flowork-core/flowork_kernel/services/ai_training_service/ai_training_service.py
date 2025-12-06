########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\ai_training_service\ai_training_service.py total lines 606 
########################################################################

import os
import threading
import json
import time
import uuid
import traceback
import zipfile
import io
import re
import queue  # [NEW] For Queue Management
from ..base_service import BaseService

pypdf_lib = None
try:
    import pypdf
    pypdf_lib = pypdf
    print("[AITraining] ✅ Using 'pypdf' library.")
except ImportError:
    try:
        import PyPDF2
        pypdf_lib = PyPDF2
        print("[AITraining] ✅ Using 'PyPDF2' library (Fallback).")
    except ImportError:
        print("[AITraining] ⚠️ Neither pypdf nor PyPDF2 found. PDF ingestion will fail.")

try:
    from docx import Document
except ImportError:
    Document = None
    print("[AITraining] ⚠️ python-docx missing. DOCX ingestion will be skipped.")

try:
    from .dataset_worker import DatasetWorker
except ImportError:
    DatasetWorker = None
    print("[AITraining] ⚠️ DatasetWorker missing.")

try:
    from .training_worker import TrainingWorker
except ImportError:
    TrainingWorker = None
    print("[AITraining] ⚠️ TrainingWorker missing.")

try:
    from .colosseum_worker import ColosseumWorker
except ImportError:
    ColosseumWorker = None
    print("[AITraining] ⚠️ ColosseumWorker missing.")

try:
    from .merge_worker import MergeWorker
except ImportError:
    MergeWorker = None
    print("[AITraining] ⚠️ MergeWorker missing.")

try:
    from .gguf_worker import GgufWorker
except ImportError:
    GgufWorker = None
    print("[AITraining] ⚠️ GgufWorker missing.")

try:
    from ..dataset_manager_service.dataset_manager_service import DatasetManagerService
except ImportError:
    DatasetManagerService = None

class AITrainingService(BaseService):
    DB_NAME = "training_jobs.json"

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)

        self.real_data_path = "/app/data"
        if hasattr(self.kernel, 'data_path'):
            self.real_data_path = self.kernel.data_path
        elif isinstance(self.kernel, dict) and 'data_path' in self.kernel:
            self.real_data_path = self.kernel['data_path']

        self.logs_dir = os.path.join(self.real_data_path, "training_logs")
        if not os.path.exists(self.logs_dir):
            try: os.makedirs(self.logs_dir, exist_ok=True)
            except: pass

        self.db_path = os.path.join(self.real_data_path, self.DB_NAME)
        self.job_lock = threading.Lock()

        self.training_queue = queue.Queue()
        self.is_processor_running = False

        if DatasetWorker:
            self.dataset_worker = DatasetWorker(self.real_data_path)
        else:
            print("[AITraining] ❌ DatasetWorker logic unavailable.")

        if hasattr(self.kernel, 'ai_models_path'):
            self.models_root = self.kernel.ai_models_path
        else:
            self.models_root = os.path.join(os.path.dirname(self.real_data_path), "flowork_kernel", "ai_models")

        self._dataset_manager_instance = None
        self._ai_manager_instance = None

        self._start_queue_processor()

        print(f"[AITraining] Service Initialized. Robust Queue Mode Active.")


    def _start_queue_processor(self):
        if self.is_processor_running: return
        self.is_processor_running = True

        def _worker_loop():
            print("[AITraining] 🟢 Queue Processor Started. Waiting for jobs...")
            while True:
                try:
                    job_packet = self.training_queue.get()

                    job_id = job_packet.get('job_id')
                    job_type = job_packet.get('type', 'UNKNOWN')
                    print(f"[AITraining] 🚀 Picking up {job_type} Job {job_id} from Queue...")

                    self._execute_job_logic(job_packet)

                    print(f"[AITraining] ✅ Job {job_id} Finished (or Failed gracefully). Checking next...")
                    self.training_queue.task_done()

                except Exception as e:
                    print(f"[AITraining] 💥 CRITICAL QUEUE ERROR: {e}")
                    traceback.print_exc()

        t = threading.Thread(target=_worker_loop, daemon=True)
        t.start()

    def _execute_job_logic(self, packet):
        """
        Executes the logic based on job type (TRAINING, GGUF, MERGE).
        Runs inside the worker thread to ensure sequential execution.
        """
        job_id = packet['job_id']
        job_type = packet.get('type', 'TRAINING')

        try:
            self.update_job_status(job_id, {
                "status": "INITIALIZING",
                "message": "Allocating Resources...",
                "progress": 5
            })

            if job_type == 'TRAINING':
                self._handle_training_task(packet)

            elif job_type == 'GGUF':
                self._handle_gguf_task(packet)

            elif job_type == 'MERGE':
                self._handle_merge_task(packet)

            else:
                raise ValueError(f"Unknown job type: {job_type}")

        except Exception as e:
            traceback.print_exc()
            self.update_job_status(job_id, {
                "status": "FAILED",
                "message": f"Engine Error: {str(e)}",
                "progress": 0
            })

    def _handle_training_task(self, packet):
        job_id = packet['job_id']
        base_model_id = packet['base_model_id']
        dataset_name = packet['dataset_name']
        new_model_name = packet['new_model_name']
        training_args = packet['training_args']

        d_mgr = self._get_dataset_manager()
        dataset_data = None

        print(f"[AITraining] Worker preparing dataset: {dataset_name}")

        if not dataset_name.lower().endswith(('.json', '.jsonl', '.txt')):
                dataset_data = d_mgr.get_dataset_data(dataset_name)

        if not dataset_data and self.dataset_worker:
            dataset_data = self.dataset_worker.load_dataset_from_file(dataset_name)

        if not dataset_data:
            possible_path = os.path.join(self.real_data_path, "datasets", dataset_name)
            possible_path_2 = os.path.join(self.real_data_path, dataset_name)
            possible_path_3 = os.path.join(self.real_data_path, "uploads", dataset_name)

            target_file = None
            if os.path.exists(possible_path): target_file = possible_path
            elif os.path.exists(possible_path_2): target_file = possible_path_2
            elif os.path.exists(possible_path_3): target_file = possible_path_3

            if target_file:
                try:
                    if target_file.endswith('.jsonl'):
                        import json
                        data = []
                        with open(target_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip(): data.append(json.loads(line))
                        dataset_data = data
                    else:
                        with open(target_file, 'r', encoding='utf-8') as f:
                            dataset_data = [{"text": f.read()}]
                except Exception as e:
                    print(f"[AITraining] Manual read failed: {e}")

        if not dataset_data:
            raise ValueError(f"Dataset '{dataset_name}' not found or empty.")

        model_full_path = self._resolve_model_path(base_model_id)

        if not TrainingWorker: raise ImportError("TrainingWorker not available")
        worker = TrainingWorker(self.real_data_path, self.models_root, self.logs_dir)
        worker.run_job(
            job_id,
            model_full_path,
            dataset_name,
            new_model_name,
            training_args,
            dataset_data,
            self.update_job_status
        )

    def _handle_gguf_task(self, packet):
        job_id = packet['job_id']
        model_id = packet['model_id']
        quantization = packet['quantization']
        final_name = packet['new_model_name']
        strategy = packet.get('strategy', 'auto')

        print(f"[AITraining] Starting GGUF Conversion for {model_id}...")

        if not GgufWorker: raise ImportError("GgufWorker not available")
        worker = GgufWorker(self.real_data_path, self.models_root, self.logs_dir)
        worker.run_job(
            job_id,
            model_id,
            quantization,
            final_name,
            self.update_job_status,
            strategy
        )

    def _handle_merge_task(self, packet):
        job_id = packet['job_id']
        model_id = packet['model_id']
        final_name = packet['new_model_name']

        print(f"[AITraining] Starting Adapter Merge for {model_id}...")

        if not MergeWorker: raise ImportError("MergeWorker not available")
        worker = MergeWorker(self.real_data_path, self.models_root, self.logs_dir)
        worker.run_job(
            job_id,
            model_id,
            final_name,
            self.update_job_status
        )

    def _resolve_model_path(self, model_id_input):
        ai_mgr = self._get_ai_manager()
        local_models = getattr(ai_mgr, 'local_models', {}) if ai_mgr else {}
        if isinstance(ai_mgr, dict): local_models = ai_mgr.get('local_models', {})

        clean_id = re.sub(r'^\(Local\s+\w+\)\s*', '', model_id_input).strip()

        if clean_id in local_models:
            return local_models[clean_id].get("full_path")

        for k, v in local_models.items():
            ck = re.sub(r'^\(Local\s+\w+\)\s*', '', k).strip()
            if clean_id == ck or (isinstance(v, dict) and clean_id == v.get('id')):
                if isinstance(v, dict) and v.get('full_path'): return v.get('full_path')

        if "/" in clean_id: return clean_id

        raise ValueError(f"Base model '{clean_id}' not found locally or as HF ID.")


    def _read_jobs_db(self):
        if not os.path.exists(self.db_path): return {}
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def _write_jobs_db(self, data):
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[AITraining] Failed to write DB: {e}")

    def update_job_status(self, job_id, updates):
        with self.job_lock:
            jobs = self._read_jobs_db()
            if job_id not in jobs and updates.get('status') == 'QUEUED':
                 jobs[job_id] = {} # Init

            if job_id in jobs:
                jobs[job_id].update(updates)
                jobs[job_id]['updated_at'] = time.time()
                self._write_jobs_db(jobs)

    def _read_job_log(self, job_id):
        try:
            log_file = os.path.join(self.logs_dir, f"{job_id}.log")
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(size - 8192, 0))
                    return f.read()
        except: pass
        return ""


    def _get_dataset_manager(self):
        if self._dataset_manager_instance: return self._dataset_manager_instance
        svc = None
        try:
            if hasattr(self.kernel, 'get_service') and callable(self.kernel.get_service):
                svc = self.kernel.get_service("dataset_manager_service")
        except Exception: pass

        if svc and hasattr(svc, 'get_dataset_data') and callable(svc.get_dataset_data):
            self._dataset_manager_instance = svc
            return svc

        if DatasetManagerService:
            class KernelStub:
                def __init__(self, orig_kernel, path_force):
                    self.orig = orig_kernel
                    self.data_path = path_force
                    self.project_root_path = os.getcwd()
                def get_service(self, x): return None
                def write_to_log(self, m, l="INFO"): print(f"[{l}] {m}")
                def __getattr__(self, name): return getattr(self.orig, name, None)

            kernel_proxy = KernelStub(self.kernel, self.real_data_path)
            manual_svc = DatasetManagerService(kernel_proxy, "dataset_manager_service")
            self._dataset_manager_instance = manual_svc
            return manual_svc
        return None

    def _get_ai_manager(self):
        if self._ai_manager_instance: return self._ai_manager_instance
        try:
            if hasattr(self.kernel, 'get_service') and callable(self.kernel.get_service):
                svc = self.kernel.get_service("ai_provider_manager_service")
                self._ai_manager_instance = svc
                return svc
        except: pass
        return None

    def _sanitize_filename(self, filename):
        clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
        return clean


    def handle_bulk_upload(self, files_list):
        """
        Handles list of dicts: [{'filename': 'x.txt', 'content': b'...'}]
        MODIFIED: Supports BOTH PyPDF2 and pypdf
        """
        if not self.dataset_worker: return "ERROR: Worker Offline"

        merged_buffer = io.BytesIO()
        base_name = "bulk_dataset"
        if files_list:
            base_name = os.path.splitext(files_list[0]['filename'])[0]

        base_name = self._sanitize_filename(base_name)
        timestamp = int(time.time())
        final_dataset_name = f"{base_name}_{timestamp}_merged.jsonl"

        print(f"[BulkUpload] Processing {len(files_list)} items for {final_dataset_name}...")
        file_count = 0

        def append_to_jsonl(filename, text_bytes):
            try:
                if isinstance(text_bytes, bytes):
                    text_str = text_bytes.decode('utf-8', errors='ignore')
                else:
                    text_str = str(text_bytes)

                if not text_str.strip(): return False

                entry = {
                    "text": f"--- START FILE: {filename} ---\n{text_str}\n--- END FILE ---\n"
                }
                json_line = json.dumps(entry, ensure_ascii=False) + "\n"
                merged_buffer.write(json_line.encode('utf-8'))
                return True
            except Exception as e:
                print(f"[BulkUpload] Skip {filename}: {e}")
                return False

        for file_obj in files_list:
            fname = file_obj['filename']
            content = file_obj['content']

            if fname.lower().endswith('.pdf'):
                if pypdf_lib:
                    try:
                        print(f"[BulkUpload] Extracting PDF ({pypdf_lib.__name__}): {fname}")
                        pdf_file = io.BytesIO(content)
                        reader = pypdf_lib.PdfReader(pdf_file)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        if append_to_jsonl(fname, text): file_count += 1
                    except Exception as e:
                        print(f"[BulkUpload] PDF Error {fname}: {e}")
                else:
                    print(f"[BulkUpload] PDF skipped (Library missing): {fname}")

            elif fname.lower().endswith(('.docx', '.doc')):
                if Document:
                    try:
                        print(f"[BulkUpload] Extracting DOCX: {fname}")
                        doc = Document(io.BytesIO(content))
                        text = "\n".join([para.text for para in doc.paragraphs])
                        if append_to_jsonl(fname, text): file_count += 1
                    except Exception as e:
                        print(f"[BulkUpload] DOCX Error {fname}: {e}")
                else:
                    print(f"[BulkUpload] DOCX skipped (python-docx missing): {fname}")

            elif fname.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(io.BytesIO(content)) as z:
                        for zinfo in z.infolist():
                            if zinfo.is_dir(): continue
                            if zinfo.filename.lower().endswith(('.txt', '.md', '.json', '.csv', '.py', '.js', '.html')):
                                with z.open(zinfo) as zf:
                                    if append_to_jsonl(zinfo.filename, zf.read()): file_count += 1
                except Exception as e:
                    print(f"[BulkUpload] Error extracting zip {fname}: {e}")

            elif fname.lower().endswith(('.txt', '.md', '.json', '.csv', '.py', '.js', '.html')):
                if append_to_jsonl(fname, content): file_count += 1

            else:
                print(f"[BulkUpload] Unsupported extension skipped: {fname}")

        print(f"[BulkUpload] Merged {file_count} valid files into JSONL.")
        merged_buffer.seek(0)
        final_bytes = merged_buffer.read()

        if file_count == 0:
             print("[BulkUpload] WARNING: No text extracted. Dataset will be empty.")

        return self.dataset_worker.save_uploaded_dataset(final_dataset_name, final_bytes)

    def save_uploaded_dataset(self, filename, content_bytes):
        return self.handle_bulk_upload([{'filename': filename, 'content': content_bytes}])

    def start_fine_tuning_job(self, base_model_id, dataset_name, new_model_name, training_args):
        """
        Starts Training via QUEUE
        """
        if not TrainingWorker: return {"error": "Training Worker not loaded."}

        try:
            if isinstance(base_model_id, dict):
                base_model_id = base_model_id.get("id") or base_model_id.get("name")

            job_id = f"ft-{uuid.uuid4()}"

            initial_data = {
                "job_id": job_id, "type": "TRAINING", "status": "QUEUED", "progress": 0,
                "message": "Waiting in Queue...", "base_model": base_model_id,
                "dataset": dataset_name, "new_model_name": new_model_name,
                "live_logs": "Job is queued. Waiting for GPU slot...", "created_at": time.time()
            }
            self.update_job_status(job_id, initial_data)

            job_packet = {
                "job_id": job_id, "type": "TRAINING",
                "base_model_id": base_model_id, "dataset_name": dataset_name,
                "new_model_name": new_model_name, "training_args": training_args
            }

            self.training_queue.put(job_packet)

            return {"job_id": job_id, "message": "Job Queued"}

        except Exception as e:
            traceback.print_exc()
            return {"error": f"Queue failed: {str(e)}"}

    def start_conversion_job(self, model_id, quantization, new_model_name=None, mode='gguf', strategy='auto'):
        """
        [MODIFIED] Starts GGUF/Merge via QUEUE
        """
        if isinstance(model_id, dict): model_id = model_id.get("id") or model_id.get("name")
        import re
        model_id = re.sub(r'^\(Local\s+\w+\)\s*', '', model_id).strip()

        final_name = new_model_name if new_model_name else f"{mode.upper()}-{model_id}"
        job_id = f"cv-{uuid.uuid4()}"
        job_type = mode.upper() # 'MERGE' or 'GGUF'

        initial_data = {
            "job_id": job_id, "type": job_type, "status": "QUEUED", "progress": 0,
            "message": f"Waiting in Queue ({job_type})...",
            "base_model": model_id,
            "quantization": quantization, "new_model_name": final_name,
            "live_logs": "Queued...", "created_at": time.time()
        }
        self.update_job_status(job_id, initial_data)

        packet = {
            "job_id": job_id,
            "type": job_type,
            "model_id": model_id,
            "quantization": quantization,
            "new_model_name": final_name,
            "strategy": strategy
        }

        self.training_queue.put(packet)
        print(f"[AITraining] {job_type} Job {job_id} pushed to queue.")

        return {"job_id": job_id}

    def run_sparring_match(self, base_model_id, adapter_model_id, prompt):
        if not ColosseumWorker: return {"error": "Colosseum Worker not available."}

        import re
        if isinstance(base_model_id, dict): base_model_id = base_model_id.get("id") or base_model_id.get("name")
        if isinstance(adapter_model_id, dict): adapter_model_id = adapter_model_id.get("id") or adapter_model_id.get("name")
        base_model_id = re.sub(r'^\(Local\s+\w+\)\s*', '', base_model_id).strip()
        adapter_model_id = re.sub(r'^\(Local\s+\w+\)\s*', '', adapter_model_id).strip()

        ai_mgr = self._get_ai_manager()
        local_models = getattr(ai_mgr, 'local_models', {}) if ai_mgr else {}
        if isinstance(ai_mgr, dict): local_models = ai_mgr.get('local_models', {})

        base_path = None
        if base_model_id in local_models:
             base_path = local_models[base_model_id].get("full_path")
        elif "/" in base_model_id:
             base_path = base_model_id

        if not base_path: return {"error": "Base model not found"}

        adapter_path = os.path.join(self.models_root, "text", adapter_model_id)
        if not os.path.exists(adapter_path):
             return {"error": f"Adapter not found at {adapter_path}"}

        worker = ColosseumWorker()
        return worker.run_sparring_match(base_path, adapter_path, prompt, base_model_id, adapter_model_id)

    def list_training_jobs(self):
        try:
            jobs = self._read_jobs_db()
            job_list = []
            for j_id, j_data in jobs.items():
                log_content = self._read_job_log(j_id)
                if log_content: j_data["live_logs"] = log_content
                elif "live_logs" not in j_data: j_data["live_logs"] = "Waiting for logs..."
                job_list.append(j_data)

            def get_sort_key(item):
                val = item.get('created_at', 0)
                try: return float(val)
                except: return 0.0
            job_list.sort(key=get_sort_key, reverse=True)
            return job_list
        except Exception as e:
            print(f"[AITraining] Error listing jobs: {e}")
            return []

    def get_job_status(self, job_id):
        jobs = self._read_jobs_db()
        job = jobs.get(job_id, {"error": "Job not found."})
        if "error" not in job:
            log_content = self._read_job_log(job_id)
            if log_content: job["live_logs"] = log_content
            else: job["live_logs"] = "Waiting for logs..."
        return job

    def delete_job(self, job_id):
        with self.job_lock:
            jobs = self._read_jobs_db()
            if job_id in jobs:
                del jobs[job_id]
                self._write_jobs_db(jobs)
                log_path = os.path.join(self.logs_dir, f"{job_id}.log")
                if os.path.exists(log_path):
                    try: os.remove(log_path)
                    except: pass
                return True
            return False
