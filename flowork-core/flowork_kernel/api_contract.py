########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\api_contract.py total lines 285 
########################################################################

"""
document : https://flowork.cloud/p-tinjauan-arsitektur-api_contractpy-kamus-induk-arsitektur-flowork-id.html
"""
from typing import List, Dict, Any, Callable, Tuple
from abc import ABC, abstractmethod
class IWebhookProvider(ABC):

    @abstractmethod
    def get_webhook_path(self, current_config: Dict[str, Any]) -> str:

        raise NotImplementedError
class BaseBrainProvider(ABC):

    def __init__(self, module_id: str, services: dict):
        self.kernel = services.get("kernel")
        self.loc = services.get("loc")
        self.logger = services.get("logger", print)
        self.module_id = module_id
        self.manifest = {}
        module_manager = self.kernel.get_service("module_manager_service") if self.kernel else None
        if module_manager:
            manifest_data = module_manager.get_manifest(self.module_id)
            if manifest_data:
                self.manifest = manifest_data
    @abstractmethod
    def get_provider_name(self) -> str:

        raise NotImplementedError
    @abstractmethod
    def is_ready(self) -> tuple[bool, str]:

        raise NotImplementedError
    @abstractmethod
    def think(self, objective: str, tools_string: str, history: list, last_observation: str) -> dict:

        raise NotImplementedError
    def get_manifest(self) -> dict:

        return self.manifest
class BaseAIProvider(ABC):

    def __init__(self, kernel, manifest: dict):
        self.kernel = kernel
        self.loc = self.kernel.get_service("localization_manager")
        self.manifest = manifest
    @abstractmethod
    def get_provider_name(self) -> str:

        raise NotImplementedError
    @abstractmethod
    def generate_response(self, prompt: str) -> dict:

        raise NotImplementedError
    @abstractmethod
    def is_ready(self) -> tuple[bool, str]:

        raise NotImplementedError
    def get_manifest(self) -> dict:

        return self.manifest
class IDataPreviewer(ABC):

    @abstractmethod
    def get_data_preview(self, config: Dict[str, Any]) -> Any:

        raise NotImplementedError
class IDynamicOutputSchema(ABC):

    @abstractmethod
    def get_dynamic_output_schema(self, current_config: Dict[str, Any]) -> List[Dict[str, Any]]:

        raise NotImplementedError
class IExecutable(ABC):

    @abstractmethod
    def execute(self, payload: Dict, config: Dict, status_updater: Callable, mode: str = 'EXECUTE', **kwargs):
        raise NotImplementedError
class IDynamicPorts(ABC):

    @abstractmethod
    def get_dynamic_ports(self, current_config):
        raise NotImplementedError
class BaseModule:

    def __init__(self, module_id: str, services: Dict[str, Any]):

        self.module_id = module_id
        for service_name, service_instance in services.items():
            setattr(self, service_name, service_instance)
        self.manifest = {}
        if hasattr(self, 'module_manager_service') and self.module_manager_service:
            manifest_data = self.module_manager_service.get_manifest(self.module_id)
            if manifest_data:
                self.manifest = manifest_data
        if not hasattr(self, 'loc'):
            self.loc = services.get("loc")
        if not hasattr(self, 'logger'):
            self.logger = services.get("logger", print)
        self._workflow_executor_cache = None
    def on_install(self):

        pass
    def on_load(self):

        pass
    def on_canvas_load(self, node_id: str):

        pass
    def on_unload(self):

        pass
    def validate(self, config: Dict[str, Any], connected_input_ports: List[str]) -> Tuple[bool, str]:

        return (True, "")
    def _get_executor(self):
        if self._workflow_executor_cache is None:
            self._workflow_executor_cache = getattr(self, 'workflow_executor_service', None)
        return self._workflow_executor_cache
    def pause_workflow(self):
        workflow_executor = self._get_executor()
        if workflow_executor:
            workflow_executor.pause_execution()
        else:
            if self.loc:
                self.logger(self.loc.get('api_contract_err_executor_not_requested', fallback="Error: The 'workflow_executor_service' was not requested by this module."), "ERROR")
            else:
                self.logger("Error: The 'workflow_executor_service' was not requested by this module.", "ERROR")
    def resume_workflow(self):
        workflow_executor = self._get_executor()
        if workflow_executor:
            workflow_executor.resume_execution()
        else:
            if self.loc:
                self.logger(self.loc.get('api_contract_err_executor_not_requested', fallback="Error: The 'workflow_executor_service' was not requested by this module."), "ERROR")
            else:
                self.logger("Error: The 'workflow_executor_service' was not requested by this module.", "ERROR")
    def request_manual_approval(self, message: str, callback: Callable[[str], None]):
        workflow_executor = self._get_executor()
        if workflow_executor:
            workflow_executor.request_manual_approval_from_module(
                self.module_id, message, callback
            )
        else:
            self.logger("Error: 'workflow_executor_service' not requested, cannot request approval.", "ERROR")
    def publish_event(self, event_name: str, event_data: Dict[str, Any]):

        event_bus = getattr(self, 'event_bus', None)
        if event_bus:
            if not isinstance(event_data, dict):
                self.logger(f"Cannot publish event '{event_name}': event_data must be a dictionary, but got {type(event_data)}. Wrapping it.", "WARN")
                event_data = {"data": event_data}
            workflow_executor = self._get_executor()
            event_data_to_publish = event_data.copy()
            if workflow_executor:
                current_context = None
                get_context_func = getattr(workflow_executor, 'get_current_execution_context', None)
                if get_context_func and callable(get_context_func):
                    current_context = get_context_func()
                if current_context:
                    event_data_to_publish['user_context'] = current_context.get('user_context')
                    event_data_to_publish['workflow_context_id'] = current_context.get('workflow_context_id')
            event_bus.publish(event_name, event_data_to_publish, publisher_id=self.module_id)
        else:
            if self.loc:
                self.logger(self.loc.get('api_contract_err_eventbus_not_requested', eventName=event_name, fallback=f"Error: The 'event_bus' service was not requested, cannot publish event '{event_name}'."), "ERROR")
            else:
                self.logger(f"Error: The 'event_bus' service was not requested, cannot publish event '{event_name}'.", "ERROR")
class BaseDashboardWidget(ABC):

    def __init__(self, kernel, widget_id: str):
        self.kernel = kernel
        self.loc = self.kernel.get_service("localization_manager")
        self.widget_id = widget_id
    @abstractmethod
    def on_widget_load(self):

        pass
    @abstractmethod
    def on_widget_destroy(self):

        pass
    @abstractmethod
    def refresh_content(self):

        pass
    @abstractmethod
    def get_widget_state(self) -> dict:

        return {}
    @abstractmethod
    def load_widget_state(self, state: dict):

        pass
class LoopConfig:

    LOOP_TYPE_COUNT = "count"
    LOOP_TYPE_CONDITION = "condition"
    def __init__(self, loop_type: str = LOOP_TYPE_COUNT, iterations: int = 1, condition_var: str = None, condition_op: str = None, condition_val: Any = None,
                 enable_sleep: bool = False, sleep_type: str = "static", static_duration: int = 1, random_min: int = 1, random_max: int = 5):
        if loop_type not in [self.LOOP_TYPE_COUNT, self.LOOP_TYPE_CONDITION]:
            raise ValueError(f"Tipe loop tidak valid: {loop_type}. Harus '{self.LOOP_TYPE_COUNT}' atau '{self.LOOP_TYPE_CONDITION}'.")
        self.loop_type = loop_type
        self.iterations = iterations
        self.condition_var = condition_var
        self.condition_op = condition_op
        self.condition_val = condition_val
        self.enable_sleep = enable_sleep
        self.sleep_type = sleep_type
        self.static_duration = static_duration
        self.random_min = random_min
        self.random_max = random_max
    def to_dict(self) -> Dict[str, Any]:

        return {
            "loop_type": self.loop_type,
            "iterations": self.iterations,
            "condition_var": self.condition_var,
            "condition_op": self.condition_op,
            "condition_val": self.condition_val,
            "enable_sleep": self.enable_sleep,
            "sleep_type": self.sleep_type,
            "static_duration": self.static_duration,
            "random_min": self.random_min,
            "random_max": self.random_max
        }
    @staticmethod
    def from_dict(data: Dict[str, Any]):

        return LoopConfig(
            loop_type=data.get("loop_type", LoopConfig.LOOP_TYPE_COUNT),
            iterations=data.get("iterations", 1),
            condition_var=data.get("condition_var"),
            condition_op=data.get("condition_op"),
            condition_val=data.get("condition_val"),
            enable_sleep=data.get("enable_sleep", False),
            sleep_type=data.get("sleep_type", "static"),
            static_duration=data.get("static_duration", 1),
            random_min=data.get("random_min", 1),
            random_max=data.get("random_max", 5)
        )
class BaseTriggerListener:

    def __init__(self, trigger_id: str, config: Dict[str, Any], services: Dict[str, Any], **kwargs):

        self.trigger_id = trigger_id
        self.config = config
        self._callback = None
        self.is_running = False
        self.rule_id = kwargs.get('rule_id')
        for service_name, service_instance in services.items():
            setattr(self, service_name, service_instance)
        self.logger = getattr(self, 'logger', print)
        self.loc = getattr(self, 'loc', None) or getattr(self, 'kernel', None) and self.kernel.get_service("localization_manager")
        if not self.rule_id:
            if self.loc:
                self.logger(self.loc.get('api_contract_warn_trigger_no_ruleid', triggerId=self.trigger_id, fallback=f"CRITICAL WARNING FOR TRIGGER '{self.trigger_id}': Listener was created without a rule_id. This trigger will be unable to run a workflow."), "ERROR")
            else:
                self.logger(f"CRITICAL WARNING FOR TRIGGER '{self.trigger_id}': Listener created without rule_id. It will not be able to run a workflow.", "ERROR")
    def set_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._callback = callback
    def start(self):
        raise NotImplementedError("Setiap Pemicu harus mengimplementasikan metode 'start'.")
    def stop(self):
        raise NotImplementedError("Setiap Pemicu harus mengimplementasikan metode 'stop'.")
    def _on_event(self, event_data: Dict[str, Any]):
        if self._callback and callable(self._callback):
            try:
                if self.rule_id:
                    event_data['rule_id'] = self.rule_id
                    user_id = None
                    state_manager = getattr(self, 'state_manager', None)
                    if state_manager:
                        pass
                    self.logger(f"Trigger '{self.trigger_id}' detected an event: {event_data}", "DEBUG")
                    self._callback(event_data)
                else:
                    self.logger(f"Trigger '{self.trigger_id}' detected an event, but it was cancelled because it has no rule_id.", "WARN")
            except Exception as e:
                self.logger(f"Error during callback execution for trigger '{self.trigger_id}': {e}", "ERROR")
