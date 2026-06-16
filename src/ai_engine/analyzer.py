"""
Log Analyzer — pattern-based log analysis with optional AI summarisation.
"""
from __future__ import annotations
import os
import re
from typing import Dict, List
from loguru import logger


# Patterns: (regex, severity, message)
LOG_PATTERNS = [
    (r"(?i)(error|exception|traceback|fatal)", "high",   "Error/exception detected"),
    (r"(?i)(warning|warn)",                    "medium", "Warning logged"),
    (r"(?i)(timeout|timed out)",               "medium", "Timeout occurred"),
    (r"(?i)(out of memory|oom)",               "high",   "Memory pressure detected"),
    (r"(?i)(connection refused|cannot connect)","high",  "Connection failure"),
    (r"(?i)(deprecated)",                      "low",    "Deprecated API usage"),
    (r"(?i)(slow query|query took)",           "medium", "Slow database query"),
]


class LogAnalyzer:
    """
    Analyse log text for issues and anomalies.

    Usage::

        analyzer = LogAnalyzer()
        report = analyzer.analyze(log_text)
    """

    def __init__(self):
        self._openai_key = os.getenv("OPENAI_API_KEY")

    def analyze(self, log_text: str) -> Dict:
        """
        Scan log text and return a structured report.
        """
        issues: List[Dict] = []
        lines = log_text.splitlines()

        for i, line in enumerate(lines, 1):
            for pattern, severity, message in LOG_PATTERNS:
                if re.search(pattern, line):
                    issues.append({
                        "line": i,
                        "severity": severity,
                        "message": message,
                        "excerpt": line.strip()[:120],
                    })
                    break  # one issue per line

        high   = [x for x in issues if x["severity"] == "high"]
        medium = [x for x in issues if x["severity"] == "medium"]
        low    = [x for x in issues if x["severity"] == "low"]

        health = "healthy"
        if high:
            health = "critical"
        elif medium:
            health = "degraded"

        recommendations: List[str] = []
        if high:
            recommendations.append(f"Investigate {len(high)} high-severity log entries immediately")
        if any("timeout" in i["message"].lower() for i in issues):
            recommendations.append("Check network connectivity and external service health")
        if any("memory" in i["message"].lower() for i in issues):
            recommendations.append("Review memory usage and consider scaling up instances")
        if any("slow query" in i["message"].lower() for i in issues):
            recommendations.append("Add database indexes and review N+1 query patterns")

        logger.info(f"Log analysis: {len(issues)} issues — health={health}")

        return {
            "health": health,
            "total_issues": len(issues),
            "by_severity": {"high": len(high), "medium": len(medium), "low": len(low)},
            "issues": issues[:50],  # cap output
            "recommendations": recommendations,
            "lines_scanned": len(lines),
        }
