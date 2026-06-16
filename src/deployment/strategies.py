"""
Deployment strategy implementations.
"""
from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List
from loguru import logger


class DeploymentStrategy(ABC):
    """Base class for all deployment strategies."""

    def __init__(self, service: str, version: str, environment: str):
        self.service = service
        self.version = version
        self.environment = environment
        self.logs: List[str] = []

    def _log(self, msg: str) -> None:
        entry = f"[{datetime.utcnow().isoformat()}] {msg}"
        self.logs.append(entry)
        logger.info(f"{self.service}: {msg}")

    @abstractmethod
    async def deploy(self) -> Dict:
        """Execute the deployment. Returns a status dict."""


class BlueGreenDeployment(DeploymentStrategy):
    """
    Blue-green deployment: spin up new (green) instances, health-check,
    shift traffic, then drain old (blue) instances.
    """

    async def deploy(self) -> Dict:
        self._log(f"Starting blue-green deployment: {self.service}@{self.version}")
        steps = [
            (2, f"Pulling image {self.service}:{self.version}"),
            (3, "Launching green instances"),
            (3, "Running health checks on green"),
            (2, "Shifting 100% traffic to green"),
            (2, "Draining blue instances"),
            (1, "Cleanup complete"),
        ]
        for delay, msg in steps:
            self._log(msg)
            await asyncio.sleep(delay)

        self._log("Blue-green deployment succeeded")
        return {
            "strategy": "blue-green",
            "service": self.service,
            "version": self.version,
            "environment": self.environment,
            "status": "deployed",
            "logs": self.logs,
        }


class RollingDeployment(DeploymentStrategy):
    """
    Rolling deployment: replace instances one by one.
    """

    def __init__(self, *args, batch_size: int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size

    async def deploy(self) -> Dict:
        self._log(f"Starting rolling deployment: {self.service}@{self.version} (batch={self.batch_size})")
        steps = [
            (2, f"Pulling image {self.service}:{self.version}"),
            (3, f"Replacing batch of {self.batch_size} instance(s)"),
            (2, "Health check passed"),
            (3, "Replacing remaining instances"),
            (1, "Rolling update complete"),
        ]
        for delay, msg in steps:
            self._log(msg)
            await asyncio.sleep(delay)

        self._log("Rolling deployment succeeded")
        return {
            "strategy": "rolling",
            "service": self.service,
            "version": self.version,
            "environment": self.environment,
            "status": "deployed",
            "logs": self.logs,
        }
