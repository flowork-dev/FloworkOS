########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\base_scanner.py total lines 32 
########################################################################

class BaseScanner:

    def __init__(self, kernel, report_callback, config=None):
        self.kernel = kernel
        self.report = report_callback
        self.loc = kernel.get_service("localization_manager")
        self.config = config if config is not None else {}
        self.critical_count = 0
        self.major_count = 0
        self.minor_count = 0
        self.info_count = 0
    def run_scan(self) -> str:

        raise NotImplementedError
    def _register_finding(self, message: str, context: dict = None):

        severity = self.config.get("severity", "MINOR").upper()
        self.report(message, severity, context)
        if severity == 'CRITICAL':
            self.critical_count += 1
        elif severity == 'MAJOR':
            self.major_count += 1
        elif severity == 'MINOR':
            self.minor_count += 1
        elif severity == 'INFO':
            self.info_count += 1
