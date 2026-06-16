"""
Pipeline runner — executes a list of PipelineStages sequentially,
updating shared context and collecting results.
"""
from __future__ import annotations
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

from .stages import PipelineStage, StageResult, StageStatus


class PipelineRunner:
    """
    Execute a list of PipelineStages in order, with optional fail-fast.

    Usage::

        runner = PipelineRunner(stages=[...], context={"repo": "..."})
        summary = await runner.run()
    """

    def __init__(
        self,
        stages: List[PipelineStage],
        context: Optional[Dict[str, Any]] = None,
        fail_fast: bool = True,
    ):
        self.stages = stages
        self.context: Dict[str, Any] = context or {}
        self.fail_fast = fail_fast
        self.results: List[StageResult] = []

    async def run(self) -> Dict[str, Any]:
        """
        Execute all stages. Returns a summary dict.
        """
        start = time.time()
        logger.info(f"Pipeline starting: {len(self.stages)} stages")

        failed = False
        for stage in self.stages:
            if failed and self.fail_fast:
                # Skip remaining stages
                from .stages import StageResult as _SR
                skipped = _SR(name=stage.name, status=StageStatus.SKIPPED)
                skipped.finish(StageStatus.SKIPPED, error="Skipped due to prior failure")
                self.results.append(skipped)
                continue

            logger.info(f"Stage start: {stage.name}")
            result = await stage.execute(self.context)
            self.results.append(result)
            self.context[f"stage_{stage.name}"] = result

            if result.status == StageStatus.FAILED:
                failed = True
                logger.error(f"Stage failed: {stage.name} — {result.error}")
            else:
                logger.info(f"Stage done: {stage.name} ({result.status})")

        elapsed = round(time.time() - start, 2)
        overall = "failed" if failed else "completed"

        summary = {
            "status": overall,
            "duration_seconds": elapsed,
            "stages": {r.name: r.status for r in self.results},
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration": r.duration_seconds,
                    "error": r.error,
                }
                for r in self.results
            ],
            "completed_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"Pipeline {overall} in {elapsed}s")
        return summary
