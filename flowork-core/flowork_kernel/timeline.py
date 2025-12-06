########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\timeline.py total lines 121 
########################################################################

import logging
import json
import os
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from collections import deque
from typing import Any, Dict, List, Deque

class JsonlFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()

class TimelineLogger:


    def __init__(self, base_path: str, namespace: str, tail_size: int = 64):
        self.base = Path(base_path).resolve()
        self.namespace = namespace
        self.tail_size = int(tail_size)

        ns = self._sanitize(namespace)
        self.dir = self.base / "timeline" / ns
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file = self.dir / "timeline.log"

        self.logger = logging.getLogger(f"agent_timeline_{namespace}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        self._tail: Deque[Dict[str, Any]] = deque(maxlen=self.tail_size)

        if not self.logger.handlers:
            handler = RotatingFileHandler(self.file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
            handler.setFormatter(JsonlFormatter())
            self.logger.addHandler(handler)

        self._prime_tail_from_disk()

    def _sanitize(self, name: str) -> str:
        return "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_", ".", "/")).replace("..",".")

    def _prime_tail_from_disk(self) -> None:
        if not self.file.exists():
            return
        try:
            lines: Deque[str] = deque(maxlen=self.tail_size)
            with self.file.open("r", encoding="utf-8") as fp:
                for line in fp:
                    lines.append(line)

            for ln in lines:
                try:
                    self._tail.append(json.loads(ln))
                except Exception:
                    continue
        except Exception as e:
            self._tail.clear()
            print(f"WARN: Failed to prime timeline tail for {self.namespace}: {e}")

    def log(self, event_type: str, data: Dict[str, Any]):

        try:
            rec = {"ts": time.time(), "type": event_type, "data": data}

            json_line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
            self.logger.info(json_line)

            self._tail.append(rec)

        except Exception as e:
            print(f"CRITICAL: Failed to log timeline event for namespace {self.namespace}: {e}")

    def export_summary(self) -> Dict[str, Any]:

        return {
            "namespace": self.namespace,
            "events": list(self._tail)
        }

    def close(self):

        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

if __name__ == "__main__":
    TEST_BASE = "logs/agents_test_r4"
    TEST_NS = "test_tenant/test_agent_123"

    test_file = Path(TEST_BASE) / "timeline" / TEST_NS / "timeline.log"
    if test_file.exists():
        os.remove(test_file)
        print(f"Removed old test log: {test_file}")

    print(f"Logging to {test_file}")

    logger = TimelineLogger(base_path=TEST_BASE, namespace=TEST_NS, tail_size=10)

    logger.log("agent_boot", {"fac_id": "fac-xyz", "gas_limit": 10000})
    logger.log("http_fetch", {"url": "https://flowork.cloud", "status": 200})
    logger.log("episodic_write", {"key": "mission_goal"})
    logger.log("agent_killed", {"reason": "OUT_OF_GAS", "gas_spent": 10005})

    summary = logger.export_summary()
    print("\n--- Export Summary (R4) ---")
    print(json.dumps(summary, indent=2))
    assert len(summary["events"]) == 4
    assert summary["events"][0]["type"] == "agent_boot"
    print("-----------------------------")

    logger.close()

    print("\nLog test complete. Check the file.")
