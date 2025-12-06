########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\services\base_service.py total lines 27 
########################################################################

import logging
class BaseService:

    def __init__(self, kernel, service_id: str):

        self.kernel = kernel
        self.service_id = service_id
        self.logger = logging.getLogger(f"{service_id}")
        self._loc_cache = None
    @property
    def loc(self):

        if self._loc_cache is None:
            self._loc_cache = self.kernel.get_service('localization_manager')
        return self._loc_cache
    def start(self):

        pass
    def stop(self):

        pass
