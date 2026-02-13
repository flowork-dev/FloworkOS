########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\ai_council\agents\base.py total lines 39 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import abc

class BaseAgent(abc.ABC):
    """
    Standard interface for AI Council Agents.
    All plugins must inherit from this class.
    """

    def __init__(self):
        self.name = "Unknown Agent"
        self.role = "Observer"
        self.icon = "mdi-account"
        self.color = "text-gray-400"
        self.border = "border-gray-500"

    @abc.abstractmethod
    def get_prompt_instruction(self) -> str:
        """
        Return the specific system instruction for this agent.
        """
        pass

    def get_profile(self):
        """
        Return the agent's UI configuration.
        """
        return {
            "name": self.name,
            "role": self.role,
            "icon": self.icon,
            "color": self.color,
            "border": self.border
        }
