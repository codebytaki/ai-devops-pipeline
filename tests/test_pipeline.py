"""
Tests for pipeline stages, runner, and deployment strategies
"""
import pytest
import asyncio
from src.pipeline.stages import PipelineStage, StageStatus, StageResult
from src.pipeline.runner import PipelineRunner
from src.ai_engine.analyzer import LogAnalyzer
from src.ai_engine.reviewer import CodeReviewer
from src.monitoring.metrics import MetricsCollector


# ── Stage tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stage_completes_successfully():
    async def dummy_handler(ctx):
        return "success"

    stage = PipelineStage(name="test", handler=dummy_handler)
    result = await stage.execute({})
    assert result.status == StageStatus.COMPLETED
    assert result.output == "success"


@pytest.mark.asyncio
async def test_stage_timeout_fails():
    async def slow_handler(ctx):
        await asyncio.sleep(10)

    stage = PipelineStage(name="slow", handler=slow_handler, timeout=0.1, on_failure="fail")
    result = await stage.execute({})
    assert result.status == StageStatus.FAILED
    assert "timed out" in (result.error or "")


@pytest.mark.asyncio
async def test_stage_timeout_skips_when_configured():
    async def slow_handler(ctx):
        await asyncio.sleep(10)

    stage = PipelineStage(name="optional", handler=slow_handler, timeout=0.1, on_failure="skip")
    result = await stage.execute({})
    assert result.status == StageStatus.SKIPPED


@pytest.mark.asyncio
async def test_stage_exception_handled():
    async def broken(ctx):
        raise ValueError("something went wrong")

    stage = PipelineStage(name="broken", handler=broken, on_failure="fail")
    result = await stage.execute({})
    assert result.status == StageStatus.FAILED
    assert "something went wrong" in (result.error or "")


# ── Runner tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_runner_all_pass():
    async def ok(ctx): return "ok"

    stages = [PipelineStage(name=f"stage{i}", handler=ok) for i in range(3)]
    runner = PipelineRunner(stages=stages)
    summary = await runner.run()
    assert summary["status"] == "completed"
    assert all(s == StageStatus.COMPLETED for s in summary["stages"].values())


@pytest.mark.asyncio
async def test_runner_fail_fast_skips_remaining():
    async def ok(ctx): return "ok"
    async def fail(ctx): raise RuntimeError("fail")

    stages = [
        PipelineStage(name="s1", handler=ok),
        PipelineStage(name="s2", handler=fail, on_failure="fail"),
        PipelineStage(name="s3", handler=ok),
    ]
    runner = PipelineRunner(stages=stages, fail_fast=True)
    summary = await runner.run()
    assert summary["status"] == "failed"
    assert summary["stages"]["s3"] == StageStatus.SKIPPED


@pytest.mark.asyncio
async def test_runner_context_passed_between_stages():
    async def write(ctx):
        ctx["value"] = 42
        return "written"

    async def read(ctx):
        assert ctx["value"] == 42
        return "read"

    stages = [
        PipelineStage(name="write", handler=write),
        PipelineStage(name="read", handler=read),
    ]
    ctx = {}
    runner = PipelineRunner(stages=stages, context=ctx)
    summary = await runner.run()
    assert summary["status"] == "completed"


# ── Log Analyzer tests ────────────────────────────────────────────────────────

def test_log_analyzer_healthy_log():
    analyzer = LogAnalyzer()
    result = analyzer.analyze("INFO: Application started\nINFO: Listening on port 8000")
    assert result["health"] == "healthy"
    assert result["total_issues"] == 0


def test_log_analyzer_detects_error():
    analyzer = LogAnalyzer()
    result = analyzer.analyze("ERROR: Database connection failed\nTraceback (most recent call last):")
    assert result["health"] == "critical"
    assert result["total_issues"] > 0
    assert result["by_severity"]["high"] > 0


def test_log_analyzer_detects_warning():
    analyzer = LogAnalyzer()
    result = analyzer.analyze("WARNING: High memory usage detected")
    assert result["health"] in ("degraded", "critical")


def test_log_analyzer_recommendations():
    analyzer = LogAnalyzer()
    result = analyzer.analyze("ERROR: Connection refused to redis:6379\nERROR: timeout connecting")
    assert len(result["recommendations"]) > 0


# ── Code Reviewer tests ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reviewer_rule_based_clean_diff():
    reviewer = CodeReviewer()
    result = await reviewer.review("def add(a, b):\n    return a + b", pr_number=1)
    assert result["status"] == "completed"
    assert result["model_used"] == "rule-based"
    assert 0 <= result["score"] <= 100


@pytest.mark.asyncio
async def test_reviewer_detects_hardcoded_password():
    reviewer = CodeReviewer()
    result = await reviewer.review('password = "s3cr3t"', pr_number=2)
    assert len(result["security_issues"]) > 0


@pytest.mark.asyncio
async def test_reviewer_detects_bare_except():
    reviewer = CodeReviewer()
    result = await reviewer.review("try:\n    pass\nexcept:\n    pass", pr_number=3)
    assert len(result["suggestions"]) > 0


# ── Metrics tests ─────────────────────────────────────────────────────────────

def test_metrics_empty():
    mc = MetricsCollector()
    s = mc.summary()
    assert s["pipelines"]["total"] == 0
    assert s["deployments"]["total"] == 0


def test_metrics_records_pipeline():
    mc = MetricsCollector()
    mc.record_pipeline("p1", "completed", 30.0)
    mc.record_pipeline("p2", "failed", 5.0)
    s = mc.summary()
    assert s["pipelines"]["total"] == 2
    assert s["pipelines"]["completed"] == 1
    assert s["pipelines"]["failed"] == 1
    assert s["pipelines"]["avg_duration_seconds"] == 17.5


def test_metrics_success_rate():
    mc = MetricsCollector()
    for i in range(8):
        mc.record_deployment(str(i), "deployed", 10.0)
    for i in range(2):
        mc.record_deployment(f"f{i}", "failed", 2.0)
    s = mc.summary()
    assert s["deployments"]["success_rate"] == 80.0
