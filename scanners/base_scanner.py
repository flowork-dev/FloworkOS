########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\scanners\base_scanner.py total lines 53 
########################################################################

from typing import Dict, Any, Callable

class BaseScanner:
    """
    Base class for all system health scanners.
    Provides standard reporting and severity tracking mechanisms.
    """

    def __init__(self, kernel, report_callback: Callable, config: Dict[str, Any] = None):
        self.kernel = kernel
        self.report = report_callback
        self.loc = kernel.get_service("localization_manager")
        self.config = config if config is not None else {}

        self.critical_count = 0
        self.major_count = 0
        self.minor_count = 0
        self.info_count = 0

    def run_scan(self) -> str:
        """
        Main entry point for the scanner.
        Must be implemented by subclasses.
        Returns a summary string.
        """
        raise NotImplementedError("Subclasses must implement run_scan()")

    def _register_finding(self, message: str, context: Dict = None, severity: str = None):
        """
        Helper to report a finding and update internal counters.
        If severity is not provided, it defaults to config or 'MINOR'.
        """
        if not severity:
            severity = self.config.get("severity", "MINOR").upper()
        else:
            severity = severity.upper()

        self.report(message, severity, context)

        if severity == 'CRITICAL':
            self.critical_count += 1
        elif severity == 'MAJOR':
            self.major_count += 1
        elif severity == 'MINOR':
            self.minor_count += 1
        elif severity == 'INFO':
            self.info_count += 1
