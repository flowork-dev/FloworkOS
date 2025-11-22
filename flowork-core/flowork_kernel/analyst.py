########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\analyst.py total lines 115 
########################################################################

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import math

class AnalystReport:

    def __init__(self, stats: Dict[str, Any], tags: List[str], risks: List[str]):
        self.stats = stats
        self.tags = tags
        self.risks = risks
    def to_dict(self) -> Dict[str, Any]:
        return {"stats": self.stats, "tags": self.tags, "risks": self.risks}

class Analyst:

    def __init__(self, budget_gas_hint: int | None = None):
        self.budget_gas_hint = budget_gas_hint or 0

    def analyze(self, events: List[Dict[str, Any]]) -> AnalystReport:
        if not events:
            return AnalystReport(stats={"empty": True}, tags=["no-activity"], risks=["no-data"])

        first_ts = events[0].get("ts", 0.0)
        last_ts = events[-1].get("ts", first_ts)
        http_cnt = 0
        fs_read_cnt = 0
        fs_write_cnt = 0
        shell_cnt = 0
        epi_r = 0
        epi_w = 0
        killed = False
        errors = 0

        gas_used = 0
        gas_left = None
        budget_gas = self.budget_gas_hint

        for ev in events:
            et = ev.get("type", "")
            data = ev.get("data", {})
            if et == "agent_boot":
                budget_gas = int(data.get("budget_gas", budget_gas or 0))
                if not budget_gas:
                    budget_gas = int(data.get("gas_limit", budget_gas or 0))
            elif et == "gas_spent":
                gas_used += int(data.get("cost", 0) or 0)
                gas_left = int(data.get("total_spent", gas_left if gas_left is not None else 0))
            elif et == "http_fetch":
                http_cnt += 1
            elif et == "fs_read":
                fs_read_cnt += 1
            elif et == "fs_write":
                fs_write_cnt += 1
            elif et == "shell_exec":
                shell_cnt += 1
            elif et == "episodic_read":
                epi_r += 1
            elif et == "episodic_write":
                epi_w += 1
            elif et in ("agent_killed", "error", "permission_denied", "permission_error"):
                killed = True
                errors += 1
            elif ev.get("error"):
                errors += 1


        duration = max(0.0, (last_ts - first_ts))

        tags: List[str] = []
        if http_cnt >= 3: tags.append("network-heavy")
        if (fs_read_cnt + fs_write_cnt) >= 3: tags.append("io-heavy")
        if shell_cnt > 0: tags.append("shell-command")
        if epi_w > 0: tags.append("memory-write")
        if epi_r > 0 and epi_w == 0: tags.append("memory-read-only")

        if budget_gas:
            use_ratio = gas_used / max(1, budget_gas)
            if use_ratio <= 0.2:
                tags.append("efficient")
            elif use_ratio >= 0.8:
                tags.append("expensive")

        risks: List[str] = []
        if killed:
            risks.append("agent_killed_or_error")
        if errors >= 3:
            risks.append("frequent_errors")
        if http_cnt >= 10:
            risks.append("excessive_network_calls")
        if (fs_read_cnt + fs_write_cnt) >= 10:
            risks.append("excessive_file_io")
        if budget_gas and gas_used >= budget_gas:
            risks.append("out_of_gas")

        stats = {
            "duration_s": round(duration, 3),
            "http_fetch": http_cnt,
            "fs_read": fs_read_cnt,
            "fs_write": fs_write_cnt,
            "shell_exec": shell_cnt,
            "episodic_read": epi_r,
            "episodic_write": epi_w,
            "gas_used": gas_used,
            "gas_left": gas_left,
            "budget_gas": budget_gas,
            "killed_or_error": killed,
            "errors": errors
        }
        return AnalystReport(stats=stats, tags=tags, risks=risks)
