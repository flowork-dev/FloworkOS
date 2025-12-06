########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\scheduler_manager_service\scheduler_manager_service.py total lines 80 
########################################################################

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime
from ..base_service import BaseService
class SchedulerManagerService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.scheduler = BackgroundScheduler(daemon=False)
        self.kernel.write_to_log("Service 'SchedulerManager' initialized.", "DEBUG")
    def start(self):

        try:
            if not self.scheduler.running:
                self.scheduler.start()
                self.kernel.write_to_log("Background scheduler started successfully.", "SUCCESS")
        except Exception as e:
            self.kernel.write_to_log(f"Failed to start scheduler: {e}", "ERROR")
    def stop(self):

        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.kernel.write_to_log("Background scheduler stopped successfully.", "INFO")
        except Exception as e:
            self.kernel.write_to_log(f"Failed to stop scheduler: {e}", "ERROR")
    def schedule_rule(self, rule_id, rule_data):

        preset_name = rule_data.get("preset_to_run")
        config = rule_data.get("config", {})
        cron_string = config.get("cron_string")
        if not all([preset_name, cron_string]):
            self.kernel.write_to_log(f"Scheduled rule '{rule_id}' is incomplete (missing preset or cron string).", "WARN")
            return
        api_service = self.kernel.get_service("api_server_service")
        if not api_service:
            self.kernel.write_to_log(f"Cannot schedule job for rule '{rule_id}', ApiServerService not available.", "ERROR")
            return
        def job_wrapper():
            self.kernel.write_to_log(f"Executing scheduled job '{rule_id}' for preset '{preset_name}'.", "INFO")
            api_service.trigger_workflow_by_api(preset_name, initial_payload={"triggered_by": "scheduler", "rule_id": rule_id})
            self.kernel.write_to_log(f"Job '{rule_id}' finished. It will run again on its next schedule.", "INFO")
        try:
            self.scheduler.add_job(
                job_wrapper,
                trigger=CronTrigger.from_crontab(cron_string),
                id=str(rule_id),
                name=f"Cron for preset: {preset_name}",
                replace_existing=True
            )
            self.kernel.write_to_log(f"Scheduled job '{rule_data.get('name')}' for preset '{preset_name}' added/updated successfully.", "SUCCESS")
        except ValueError as e:
             self.kernel.write_to_log(f"Invalid Cron String format for rule '{rule_data.get('name')}': {e}", "ERROR")
        except Exception as e:
            self.kernel.write_to_log(f"Failed to add scheduled job '{rule_id}': {e}", "ERROR")
    def remove_scheduled_rule(self, rule_id):

        try:
            self.scheduler.remove_job(str(rule_id))
            self.kernel.write_to_log(f"Scheduled job with ID '{rule_id}' removed successfully.", "INFO")
        except JobLookupError:
            self.kernel.write_to_log(f"Attempted to remove a scheduled job '{rule_id}' that does not exist.", "WARN")
        except Exception as e:
            self.kernel.write_to_log(f"Failed to remove scheduled job '{rule_id}': {e}", "ERROR")
    def get_next_run_time(self, job_id: str) -> datetime | None:

        try:
            for job in self.scheduler.get_jobs():
                if job.id == str(job_id):
                    return job.next_run_time
        except Exception as e:
            self.kernel.write_to_log(f"Error while searching for scheduled job '{job_id}': {e}", "ERROR")
        return None
