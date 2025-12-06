########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\job_orchestrator_service\job_orchestrator_service.py total lines 294 
########################################################################

import os
import sqlite3
import json
import time
import uuid
import threading
import traceback
from ..base_service import BaseService

class JobOrchestratorService(BaseService):

    PRIORITY_HIGH = 100   # Chat / Realtime Interaction
    PRIORITY_MEDIUM = 50  # Agent Loop / Workflow
    PRIORITY_LOW = 10     # Training / Bulk Processing

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)

        self.data_path = "/app/data"
        if hasattr(self.kernel, 'data_path'):
            self.data_path = self.kernel.data_path

        self.db_path = os.path.join(self.data_path, "global_jobs.db")

        self.db_lock = threading.Lock()

        self.resource_status = {
            "GPU": "IDLE",  # IDLE, BUSY
            "CPU": "IDLE"
        }

        self._init_db()

        self.running = True
        self.worker_thread = threading.Thread(target=self._orchestrator_loop, daemon=True)
        self.worker_thread.start()

        print(f"[JobOrchestrator] ✅ Service Online. Database: {self.db_path}")

    def _init_db(self):
        """Bikin tabel kalau belum ada"""
        with self.db_lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS global_jobs (
                        job_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        job_type TEXT,
                        status TEXT,
                        priority INTEGER,
                        resource_req TEXT,
                        payload TEXT,
                        created_at REAL,
                        started_at REAL,
                        finished_at REAL,
                        error_msg TEXT
                    )
                ''')

                cursor.execute('''
                    UPDATE global_jobs
                    SET status = 'FAILED', error_msg = 'Engine Restarted unexpectedly'
                    WHERE status = 'RUNNING'
                ''')

                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[JobOrchestrator] ❌ DB Init Error: {e}")


    def submit_job(self, user_id, job_type, payload, priority=10, resource_req="GPU"):
        """
        Service lain manggil ini buat daftar antrian.
        Returns: job_id
        """
        job_id = str(uuid.uuid4())
        created_at = time.time()

        payload_json = json.dumps(payload)

        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO global_jobs
                (job_id, user_id, job_type, status, priority, resource_req, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_id, user_id, job_type, 'QUEUED', priority, resource_req, payload_json, created_at))
            conn.commit()
            conn.close()

        print(f"[JobOrchestrator] 📥 Job Submitted: {job_type} (ID: {job_id}) by User: {user_id}")
        return job_id

    def get_job_status(self, job_id):
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM global_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

    def cancel_job(self, job_id, user_id):
        """User bisa cancel job sendiri"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT user_id, status FROM global_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return {"success": False, "error": "Job not found"}

            owner, status = row
            if owner != user_id:
                conn.close()
                return {"success": False, "error": "Unauthorized"}

            if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
                conn.close()
                return {"success": False, "error": "Job already finished"}

            cursor.execute("UPDATE global_jobs SET status = 'CANCELLED', finished_at = ? WHERE job_id = ?", (time.time(), job_id))
            conn.commit()
            conn.close()


            return {"success": True}

    def get_queue_list(self, limit=10):
        """Buat nampilin di GUI Dashboard"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT job_id, user_id, job_type, status, created_at, resource_req
                FROM global_jobs
                WHERE status IN ('QUEUED', 'RUNNING')
                ORDER BY status DESC, priority DESC, created_at ASC
                LIMIT ?
            ''', (limit,))
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows


    def _orchestrator_loop(self):
        """Loop abadi untuk ngecek antrian dan dispatch job"""
        print("[JobOrchestrator] 👮 Traffic Control Started...")

        while self.running:
            try:
                if self.resource_status["GPU"] == "BUSY":
                    time.sleep(1) # Tunggu bentar
                    continue

                next_job = self._fetch_next_job()

                if next_job:
                    self._execute_job(next_job)
                else:
                    time.sleep(1) # Queue kosong, istirahat

            except Exception as e:
                print(f"[JobOrchestrator] 💥 Loop Error: {e}")
                traceback.print_exc()
                time.sleep(5)

    def _fetch_next_job(self):
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM global_jobs
                WHERE status = 'QUEUED'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            ''')
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

    def _execute_job(self, job):
        job_id = job['job_id']
        job_type = job['job_type']

        print(f"[JobOrchestrator] 🚦 Starting Job: {job_id} ({job_type})")

        self._update_job_status(job_id, 'RUNNING')

        if job['resource_req'] == 'GPU':
            self.resource_status["GPU"] = "BUSY"

        try:
            success = False
            error_msg = None

            if job_type.startswith('TRAINING_'):
                success = self._dispatch_to_training_service(job)
            elif job_type.startswith('INFERENCE_') or job_type == 'CHAT':
                success = self._dispatch_to_ai_service(job)
            elif job_type == 'WORKFLOW':
                success = self._dispatch_to_workflow_service(job)
            else:
                error_msg = f"Unknown job type: {job_type}"

            if not success and not error_msg:
                error_msg = "Worker returned failure"

            status = 'COMPLETED' if success else 'FAILED'
            self._update_job_status(job_id, status, error=error_msg)

        except Exception as e:
            traceback.print_exc()
            self._update_job_status(job_id, 'FAILED', error=str(e))

        finally:
            if job['resource_req'] == 'GPU':
                self.resource_status["GPU"] = "IDLE"
            print(f"[JobOrchestrator] 🏁 Job {job_id} Finished. GPU Unlocked.")

    def _update_job_status(self, job_id, status, error=None):
        with self.db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            updates = ["status = ?", "finished_at = ?" if status in ['COMPLETED', 'FAILED'] else "started_at = ?"]
            params = [status, time.time()]

            if error:
                updates.append("error_msg = ?")
                params.append(error)

            params.append(job_id)

            query = f"UPDATE global_jobs SET {', '.join(updates)} WHERE job_id = ?"
            cursor.execute(query, tuple(params))
            conn.commit()
            conn.close()


    def _dispatch_to_training_service(self, job):
        """
        Manggil fungsi internal AI Training Service.
        Kita pake kernel.get_service biar loose coupling.
        """
        svc = self.kernel.get_service("ai_training_service")
        if not svc:
            print("❌ AI Training Service not found!")
            return False

        payload = json.loads(job['payload'])

        try:
            return svc.execute_job_direct(job['job_id'], payload)
        except AttributeError:
            print("⚠️ Method execute_job_direct belum ada di TrainingService")
            return False
        except Exception as e:
            print(f"Error dispatch training: {e}")
            return False

    def _dispatch_to_ai_service(self, job):
        svc = self.kernel.get_service("ai_provider_manager_service")
        if not svc: return False
        return True

    def _dispatch_to_workflow_service(self, job):
        svc = self.kernel.get_service("workflow_executor_service")
        if not svc: return False
        return True
