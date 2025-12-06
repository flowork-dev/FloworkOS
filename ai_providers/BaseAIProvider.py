########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\BaseAIProvider.py total lines 28 
########################################################################

from abc import ABC, abstractmethod
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
