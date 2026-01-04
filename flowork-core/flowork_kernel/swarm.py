########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\flowork_kernel\swarm.py total lines 239 
########################################################################

from __future__ import annotations
from typing import Dict, Any, List, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, Future, TimeoutError as FutTimeout
from collections import deque
import time
import uuid
import math
import threading
import traceback

try:
    from .gremlin import maybe_chaos_inject
except Exception:
    def maybe_chaos_inject(stage: str) -> None:
        return

SendTaskFn = Callable[[str, Dict[str, Any]], Dict[str, Any]]

def _now_ms() -> float:
    return time.time() * 1000.0

def _p95(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(math.ceil(0.95 * len(s)) - 1))
    return s[idx]

class SwarmCoordinator:

    def __init__(self,
                 send_task_fn: SendTaskFn,
                 *,
                 max_workers: Optional[int] = None,
                 default_timeout_s: float = 30.0,
                 retries: int = 0,
                 backoff_base_s: float = 0.5,
                 timeline: Optional[Any] = None):
        self.send_task_fn = send_task_fn
        self.max_workers = max_workers
        self.default_timeout_s = float(default_timeout_s)
        self.retries = int(max(0, retries))
        self.backoff_base_s = float(max(0.0, backoff_base_s))
        self.timeline = timeline

    def fan_out(self,
                engine_ids: List[str],
                task: Dict[str, Any],
                *,
                quorum: str = "all",
                per_engine_timeout_s: Optional[float] = None,
                retries: Optional[int] = None,
                backoff_base_s: Optional[float] = None) -> Dict[str, Any]:

        swarm_id = str(uuid.uuid4())
        t_start = _now_ms()
        self._log("swarm_start", {"swarm_id": swarm_id, "size": len(engine_ids), "quorum": quorum})

        timeout_s = float(per_engine_timeout_s or self.default_timeout_s)
        rtries = int(self.retries if retries is None else max(0, retries))
        bbase = float(self.backoff_base_s if backoff_base_s is None else max(0.0, backoff_base_s))

        max_workers = self.max_workers or max(1, len(engine_ids))
        results: Dict[str, Dict[str, Any]] = {}
        latencies: List[float] = []
        success_count = 0
        failure_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_map: Dict[Future, Tuple[str, Dict[str, Any]]] = {}
            for eid in engine_ids:
                payload = dict(task)
                payload.setdefault("task_id", str(uuid.uuid4()))
                payload.setdefault("swarm_id", swarm_id)
                fut = pool.submit(self._call_with_retry, eid, payload, timeout_s, rtries, bbase)
                future_map[fut] = (eid, payload)

            for fut in as_completed(future_map):
                eid, payload = future_map[fut]
                t0 = _now_ms()
                try:
                    ok, value, err, latency_ms = fut.result(timeout=timeout_s + 0.1)
                except Exception as e:
                    ok, value, err = False, None, f"executor_error: {e}"
                    latency_ms = _now_ms() - t0

                latencies.append(latency_ms)
                if ok:
                    success_count += 1
                    results[eid] = {"ok": True, "value": value, "error": None, "latency_ms": round(latency_ms, 2)}
                else:
                    failure_count += 1
                    results[eid] = {"ok": False, "value": None, "error": str(err), "latency_ms": round(latency_ms, 2)}

                if quorum == "any" and success_count >= 1:
                    pass

        total = len(engine_ids)
        quorum_met = self._check_quorum(quorum, total, success_count)
        t_total = _now_ms() - t_start

        summary = {
            "total": total,
            "success": success_count,
            "failure": failure_count,
            "quorum": quorum,
            "quorum_met": quorum_met,
            "latency_ms_avg": round(sum(latencies)/len(latencies), 2) if latencies else 0.0,
            "latency_ms_p95": round(_p95(latencies), 2) if latencies else 0.0,
            "duration_ms": round(t_total, 2)
        }

        out = {
            "swarm_id": swarm_id,
            "task": {k: v for k, v in task.items() if k not in ("swarm_id",)},
            "results": results,
            "summary": summary
        }
        self._log("swarm_result", {"swarm_id": swarm_id, "summary": summary})
        self._log("swarm_finish", {"swarm_id": swarm_id})
        return out

    def any_success(self, engine_ids: List[str], task: Dict[str, Any], **kw) -> Dict[str, Any]:

        kw.setdefault("quorum", "any")
        return self.fan_out(engine_ids, task, **kw)

    def majority(self, engine_ids: List[str], task: Dict[str, Any], **kw) -> Dict[str, Any]:

        kw.setdefault("quorum", "majority")
        return self.fan_out(engine_ids, task, **kw)

    def map_reduce(self,
                   engine_ids: List[str],
                   task_builder: Callable[[str], Dict[str, Any]],
                   reducer: Callable[[List[Tuple[str, Dict[str, Any]]]], Any],
                   *,
                   quorum: str = "all",
                   per_engine_timeout_s: Optional[float] = None,
                   retries: Optional[int] = None,
                   backoff_base_s: Optional[float] = None) -> Dict[str, Any]:

        swarm_id = str(uuid.uuid4())
        tasks = {eid: task_builder(eid) for eid in engine_ids}
        def send_mux(eid: str, _: Dict[str, Any]) -> Dict[str, Any]:
            p = dict(tasks[eid])
            p.setdefault("task_id", str(uuid.uuid4()))
            p.setdefault("swarm_id", swarm_id)
            return self.send_task_fn(eid, p)

        tmp = SwarmCoordinator(
            send_mux,
            max_workers=self.max_workers,
            default_timeout_s=per_engine_timeout_s or self.default_timeout_s,
            retries=self.retries if retries is None else retries,
            backoff_base_s=self.backoff_base_s if backoff_base_s is None else backoff_base_s,
            timeline=self.timeline
        )
        res = tmp.fan_out(engine_ids, task={"map_reduce": True}, quorum=quorum)
        oks: List[Tuple[str, Dict[str, Any]]] = []
        for eid, r in res["results"].items():
            if r.get("ok"):
                oks.append((eid, r["value"]))
        agg = None
        try:
            agg = reducer(oks)
        except Exception as e:
            agg = {"error": f"reducer_error: {e}"}
        res["aggregate"] = agg
        return res

    def _log(self, event: str, data: Dict[str, Any]) -> None:
        if self.timeline is not None and hasattr(self.timeline, "log"):
            try:
                self.timeline.log(event, data)
            except Exception:
                pass

    def _check_quorum(self, quorum: str, total: int, success: int) -> bool:
        if quorum == "all":
            return success == total
        if quorum == "any":
            return success >= 1
        if quorum == "majority":
            return success > total // 2
        return success == total

    def _call_with_retry(self,
                         engine_id: str,
                         payload: Dict[str, Any],
                         timeout_s: float,
                         retries: int,
                         backoff_base_s: float) -> Tuple[bool, Any, Optional[str], float]:

        attempts = 0
        last_err: Optional[str] = None
        t0 = _now_ms()
        while True:
            maybe_chaos_inject("swarm_before_send")
            try:
                v = self.send_task_fn(engine_id, payload)
                if isinstance(v, dict) and ("error" in v) and v["error"]:
                    raise RuntimeError(str(v["error"]))
                latency_ms = _now_ms() - t0
                return True, v, None, latency_ms
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                attempts += 1
                if attempts > retries:
                    latency_ms = _now_ms() - t0
                    return False, None, last_err, latency_ms
                delay = min(backoff_base_s * (2 ** (attempts - 1)), max(0.0, timeout_s / 2.0))
                time.sleep(delay)
                continue

class LocalSwarmRegistry:

    def __init__(self):
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def register(self, engine_id: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        with self._lock:
            self._handlers[engine_id] = handler

    def make_send_task_fn(self) -> SendTaskFn:
        def send(engine_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            with self._lock:
                h = self._handlers.get(engine_id)
            if not h:
                return {"error": f"engine '{engine_id}' not registered"}
            return h(payload)
        return send
