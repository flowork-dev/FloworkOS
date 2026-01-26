########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\exceptions.py total lines 36 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
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
