########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\exceptions.py total lines 36 
########################################################################

class FloworkException(Exception):

    pass
class PresetNotFoundError(FloworkException):

    pass
class ModuleValidationError(FloworkException):

    pass
class ApiKeyMissingError(FloworkException):

    pass
class DependencyError(FloworkException):

    pass
class SignatureVerificationError(FloworkException):

    pass
class MandatoryUpdateRequiredError(FloworkException):

    def __init__(self, message, update_info=None):
        super().__init__(message)
        self.update_info = update_info or {}
class PermissionDeniedError(FloworkException):

    pass

class OpsServiceError(FloworkException):

    pass
