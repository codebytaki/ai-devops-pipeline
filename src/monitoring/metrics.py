"""
Metrics collector — aggregates pipeline/deployment data and exposes Prometheus-style counters.
"""
from __future__ import annotations
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any


class MetricsCollector:
    """
    Simple in-process metrics store.
    In production, back this with Redis or Prometheus push gateway.

    Usage::

        mc = MetricsCollector()
        mc.record_pipeline("p1", status="completed", duration=42.0)
        print(mc.summary())
    """

    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._durations: Dict[str, List[float]] = defaultdict(list)
        self._start = time.time()

    # ── Writers ───────────────────────────────────────────────────────────────

    def record_pipeline(self, pipeline_id: str, status: str, duration: float) -> None:
        self._counters["pipelines_total"] += 1
        self._counters[f"pipelines_{status}"] += 1
        self._durations["pipeline_duration"].append(duration)

    def record_deployment(self, deploy_id: str, status: str, duration: float) -> None:
        self._counters["deployments_total"] += 1
        self._counters[f"deployments_{status}"] += 1
        self._durations["deployment_duration"].append(duration)

    def increment(self, key: str, value: int = 1) -> None:
        self._counters[key] += value

    # ── Readers ───────────────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        pipe_durations = self._durations.get("pipeline_duration", [])
        deploy_durations = self._durations.get("deployment_duration", [])

        def _avg(lst: List[float]) -> float:
            return round(sum(lst) / len(lst), 2) if lst else 0.0

        total_pipes = self._counters.get("pipelines_total", 0)
        success_pipes = self._counters.get("pipelines_completed", 0)

        total_deploys = self._counters.get("deployments_total", 0)
        success_deploys = self._counters.get("deployments_deployed", 0)

        uptime = round(time.time() - self._start, 1)

        return {
            "uptime_seconds": uptime,
            "pipelines": {
                "total": total_pipes,
                "completed": success_pipes,
                "failed": self._counters.get("pipelines_failed", 0),
                "success_rate": round(success_pipes / total_pipes * 100, 1) if total_pipes else 0.0,
                "avg_duration_seconds": _avg(pipe_durations),
            },
            "deployments": {
                "total": total_deploys,
                "successful": success_deploys,
                "failed": self._counters.get("deployments_failed", 0),
                "success_rate": round(success_deploys / total_deploys * 100, 1) if total_deploys else 0.0,
                "avg_duration_seconds": _avg(deploy_durations),
            },
            "recorded_at": datetime.utcnow().isoformat(),
        }
