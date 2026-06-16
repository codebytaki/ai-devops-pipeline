"""
Pipeline stage definitions and execution primitives
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Callable, Awaitable, List, Optional


class StageStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    name: str
    status: StageStatus
    duration_seconds: float = 0.0
    output: str = ""
    error: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

    def finish(self, status: StageStatus, output: str = "", error: Optional[str] = None) -> None:
        self.status = status
        self.output = output
        self.error = error
        self.completed_at = datetime.utcnow().isoformat()


@dataclass
class PipelineStage:
    """
    A single pipeline stage with a name, handler coroutine, and optional timeout.

    Example::

        async def run_tests(ctx):
            # ... run pytest, return output
            return "All tests passed"

        stage = PipelineStage(name="test", handler=run_tests, timeout=120)
    """
    name: str
    handler: Callable[..., Awaitable[str]]
    timeout: float = 60.0
    on_failure: str = "fail"   # "fail" | "warn" | "skip"

    async def execute(self, context: dict) -> StageResult:
        result = StageResult(name=self.name, status=StageStatus.IN_PROGRESS)
        try:
            output = await asyncio.wait_for(self.handler(context), timeout=self.timeout)
            result.finish(StageStatus.COMPLETED, output=str(output or ""))
        except asyncio.TimeoutError:
            msg = f"Stage '{self.name}' timed out after {self.timeout}s"
            if self.on_failure == "skip":
                result.finish(StageStatus.SKIPPED, error=msg)
            elif self.on_failure == "warn":
                result.finish(StageStatus.COMPLETED, output=f"[WARN] {msg}")
            else:
                result.finish(StageStatus.FAILED, error=msg)
        except Exception as exc:
            if self.on_failure == "skip":
                result.finish(StageStatus.SKIPPED, error=str(exc))
            elif self.on_failure == "warn":
                result.finish(StageStatus.COMPLETED, output=f"[WARN] {exc}")
            else:
                result.finish(StageStatus.FAILED, error=str(exc))
        return result
