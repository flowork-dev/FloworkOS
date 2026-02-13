########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\ai_providers\BaseAIProvider.py total lines 34 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
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

    @abstractmethod
    def get_embedding(self, text: str) -> list:
        """Fungsi baru untuk mendukung Neural Knowledge Router (RAG)"""
        raise NotImplementedError

    def get_manifest(self) -> dict:
        return self.manifest
