########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\community_addon_service\community_addon_service.py total lines 27 
########################################################################

import os
from ..base_service import BaseService
class CommunityAddonService(BaseService):

    def __init__(self, kernel, service_id: str):
        super().__init__(kernel, service_id)
        self.logger = self.kernel.write_to_log
        self.logger("CommunityAddonService: Initialized (Upload Disabled in Open Core MVP).", "INFO")
    def upload_component(self, comp_type, component_id, description, tier):

        self.logger(f"Attempted to upload component '{component_id}' - Operation disabled in Open Core MVP.", "WARN")
        return False, "Component upload to the marketplace is disabled in this version."
    def upload_model(
        self, model_filepath: str, model_id: str, description: str, tier: str
    ):

        self.logger(f"Attempted to upload model '{model_id}' - Operation disabled in Open Core MVP.", "WARN")
        return (
            False,
            "Model upload to the marketplace is disabled in this version.",
        )
