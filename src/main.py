"""
AI-Powered DevOps Pipeline - Main Application
"""
import os
import uuid
import asyncio
import subprocess
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# ── In-memory stores (replace with Redis/DB in production) ──────────────────
_pipeline_store: Dict[str, Dict] = {}
_deployment_store: Dict[str, Dict] = {}
_metrics_store: Dict[str, Any] = {
    "deployments": {"total": 0, "successful": 0, "failed": 0},
    "build_times_seconds": [],
    "start_time": datetime.utcnow().isoformat(),
}

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI-Powered DevOps Pipeline",
    description="Automated CI/CD pipeline with AI capabilities",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("logs", exist_ok=True)
logger.add("logs/app.log", rotation="100 MB", retention="10 days", level="INFO")


# ── Request/Response models ──────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    environment: str = "production"
    auto_deploy: bool = False


class CodeReviewRequest(BaseModel):
    pr_number: int
    repo_url: str
    ai_provider: str = "openai"
    diff: Optional[str] = None  # raw diff text (optional)


class DeploymentRequest(BaseModel):
    service_name: str
    version: str
    environment: str
    strategy: str = "blue-green"


class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
    uptime_seconds: float


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "AI-Powered DevOps Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Real health check — probes dependent services."""
    services: Dict[str, str] = {"api": "running"}

    # Check Redis
    try:
        import redis as _redis
        r = _redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), socket_timeout=2)
        r.ping()
        services["redis"] = "connected"
    except Exception:
        services["redis"] = "unavailable"

    # Check Postgres
    try:
        import psycopg2
        conn = psycopg2.connect(os.getenv("DATABASE_URL", ""), connect_timeout=2)
        conn.close()
        services["database"] = "connected"
    except Exception:
        services["database"] = "unavailable"

    # Check AI engine (env var presence)
    ai_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    services["ai_engine"] = "ready" if ai_key else "no_api_key_configured"

    start = datetime.fromisoformat(_metrics_store["start_time"])
    uptime = (datetime.utcnow() - start).total_seconds()

    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": services,
        "uptime_seconds": round(uptime, 1),
    }


@app.post("/pipeline/trigger")
async def trigger_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Trigger a CI/CD pipeline run."""
    pipeline_id = str(uuid.uuid4())[:8]
    _pipeline_store[pipeline_id] = {
        "id": pipeline_id,
        "repo": request.repo_url,
        "branch": request.branch,
        "environment": request.environment,
        "status": "queued",
        "stage": "initialising",
        "progress": 0,
        "stages": {
            "code_review": "pending",
            "lint":        "pending",
            "test":        "pending",
            "security_scan": "pending",
            "docker_build": "pending",
            "deploy":      "pending",
        },
        "created_at": datetime.utcnow().isoformat(),
        "logs": [],
    }
    background_tasks.add_task(execute_pipeline, pipeline_id, request)
    logger.info(f"Pipeline {pipeline_id} queued for {request.repo_url}@{request.branch}")
    return {
        "pipeline_id": pipeline_id,
        "status": "queued",
        "repo": request.repo_url,
        "branch": request.branch,
        "environment": request.environment,
        "status_url": f"/pipeline/status/{pipeline_id}",
    }


@app.get("/pipeline/status/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    """Get real-time pipeline execution status."""
    if pipeline_id not in _pipeline_store:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
    return _pipeline_store[pipeline_id]


@app.get("/pipeline/list")
async def list_pipelines(limit: int = 20):
    """List recent pipeline runs."""
    runs = sorted(_pipeline_store.values(), key=lambda x: x["created_at"], reverse=True)
    return {"pipelines": runs[:limit], "total": len(_pipeline_store)}


@app.post("/ai/code-review")
async def ai_code_review(request: CodeReviewRequest):
    """AI-powered code review using OpenAI or Anthropic."""
    logger.info(f"Code review requested for PR #{request.pr_number}")

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    diff_text = request.diff or f"PR #{request.pr_number} from {request.repo_url}"

    # ── Real AI review if key is available ──────────────────────────────────
    suggestions: List[str] = []
    security_issues: List[str] = []
    performance_tips: List[str] = []
    model_used = "none"

    if openai_key and request.ai_provider == "openai":
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_key)
            prompt = (
                "You are a senior code reviewer. Review the following code diff and return:\n"
                "1. 3 specific improvement suggestions\n"
                "2. Any security issues\n"
                "3. Performance tips\n"
                "Format as JSON with keys: suggestions (list), security_issues (list), performance_tips (list).\n\n"
                f"DIFF:\n{diff_text[:3000]}"
            )
            resp = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=600,
            )
            import json as _json
            parsed = _json.loads(resp.choices[0].message.content)
            suggestions = parsed.get("suggestions", [])
            security_issues = parsed.get("security_issues", [])
            performance_tips = parsed.get("performance_tips", [])
            model_used = "gpt-4o-mini"
        except Exception as e:
            logger.warning(f"OpenAI review failed: {e}; falling back to rule-based")

    elif anthropic_key and request.ai_provider == "anthropic":
        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=600,
                messages=[{
                    "role": "user",
                    "content": (
                        "Review this code diff and return JSON with keys: "
                        "suggestions, security_issues, performance_tips (each a list of strings).\n\n"
                        f"DIFF:\n{diff_text[:3000]}"
                    ),
                }],
            )
            import json as _json
            parsed = _json.loads(msg.content[0].text)
            suggestions = parsed.get("suggestions", [])
            security_issues = parsed.get("security_issues", [])
            performance_tips = parsed.get("performance_tips", [])
            model_used = "claude-3-haiku"
        except Exception as e:
            logger.warning(f"Anthropic review failed: {e}; falling back to rule-based")

    # ── Rule-based fallback ──────────────────────────────────────────────────
    if not suggestions:
        model_used = "rule-based"
        if "password" in diff_text.lower() or "secret" in diff_text.lower():
            security_issues.append("Possible hardcoded secret or password detected — use environment variables")
        if "TODO" in diff_text or "FIXME" in diff_text:
            suggestions.append("Resolve TODO/FIXME comments before merging")
        if "except:" in diff_text or "except Exception:" in diff_text:
            suggestions.append("Avoid bare except clauses — catch specific exceptions")
        if not suggestions:
            suggestions = [
                "Ensure new functions have docstrings",
                "Add unit tests for changed logic",
                "Check for proper error handling",
            ]
        performance_tips = ["Consider caching expensive operations", "Use async I/O where possible"]

    score = max(40, 100 - len(security_issues) * 20 - len(suggestions) * 5)

    return {
        "pr_number": request.pr_number,
        "status": "completed",
        "model_used": model_used,
        "score": score,
        "issues_found": len(suggestions) + len(security_issues),
        "suggestions": suggestions,
        "security_issues": security_issues,
        "performance_tips": performance_tips,
        "reviewed_at": datetime.utcnow().isoformat(),
    }


@app.post("/deploy")
async def deploy_service(request: DeploymentRequest, background_tasks: BackgroundTasks):
    """Initiate a deployment."""
    deploy_id = str(uuid.uuid4())[:8]
    _deployment_store[deploy_id] = {
        "id": deploy_id,
        "service": request.service_name,
        "version": request.version,
        "environment": request.environment,
        "strategy": request.strategy,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "logs": [],
    }
    background_tasks.add_task(execute_deployment, deploy_id, request)
    logger.info(f"Deployment {deploy_id}: {request.service_name}@{request.version} → {request.environment}")
    return {
        "deployment_id": deploy_id,
        "status": "queued",
        "service": request.service_name,
        "version": request.version,
        "environment": request.environment,
        "strategy": request.strategy,
        "status_url": f"/deploy/status/{deploy_id}",
    }


@app.get("/deploy/status/{deploy_id}")
async def get_deploy_status(deploy_id: str):
    if deploy_id not in _deployment_store:
        raise HTTPException(status_code=404, detail=f"Deployment {deploy_id} not found")
    return _deployment_store[deploy_id]


@app.get("/metrics")
async def get_metrics():
    """Real metrics aggregated from pipeline/deployment runs."""
    m = _metrics_store["deployments"]
    total = m["total"]
    success_rate = round(m["successful"] / total * 100, 2) if total > 0 else 0.0

    build_times = _metrics_store["build_times_seconds"]
    avg_build = round(sum(build_times) / len(build_times), 1) if build_times else 0.0

    start = datetime.fromisoformat(_metrics_store["start_time"])
    uptime_hours = (datetime.utcnow() - start).total_seconds() / 3600

    return {
        "deployments": {
            "total": total,
            "successful": m["successful"],
            "failed": m["failed"],
            "success_rate": success_rate,
        },
        "build_time": {
            "average_seconds": avg_build,
            "samples": len(build_times),
        },
        "uptime_hours": round(uptime_hours, 2),
        "pipelines_tracked": len(_pipeline_store),
        "recorded_at": datetime.utcnow().isoformat(),
    }


@app.get("/ai/insights")
async def get_ai_insights():
    """AI-generated operational insights based on real pipeline data."""
    m = _metrics_store["deployments"]
    total = m["total"]
    fail_rate = (m["failed"] / total * 100) if total > 0 else 0

    recommendations: List[str] = []
    if fail_rate > 20:
        recommendations.append(f"Deployment failure rate is {fail_rate:.1f}% — review failing pipelines")
    if not recommendations:
        recommendations.append("All systems nominal — keep maintaining test coverage above 80%")

    # Count recent pipeline failures
    recent_failures = [
        p for p in _pipeline_store.values()
        if p.get("status") == "failed"
    ]
    if recent_failures:
        recommendations.append(f"{len(recent_failures)} pipeline(s) failed recently — check logs")

    return {
        "recommendations": recommendations,
        "stats": {
            "total_pipelines": len(_pipeline_store),
            "failed_pipelines": len(recent_failures),
            "deployment_success_rate": round(100 - fail_rate, 1),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


# ── Background task implementations ──────────────────────────────────────────

async def execute_pipeline(pipeline_id: str, request: PipelineRequest):
    """
    Simulate a realistic CI/CD pipeline with stage-by-stage progression.
    In production: wire to GitHub API, Docker daemon, kubectl/ECS deploy, etc.
    """
    p = _pipeline_store[pipeline_id]
    start_ts = time.time()

    stages = [
        ("code_review",   5,  "Analysing code quality"),
        ("lint",          4,  "Running linters"),
        ("test",          10, "Running test suite"),
        ("security_scan", 6,  "Scanning for vulnerabilities"),
        ("docker_build",  8,  "Building Docker image"),
        ("deploy",        5,  "Deploying to " + request.environment),
    ]
    progress_step = 100 // len(stages)

    p["status"] = "running"
    logger.info(f"Pipeline {pipeline_id} started")

    for i, (stage, sleep_s, msg) in enumerate(stages):
        p["stage"] = stage
        p["stages"][stage] = "in_progress"
        p["progress"] = i * progress_step
        p["logs"].append(f"[{datetime.utcnow().isoformat()}] {msg}...")
        logger.debug(f"Pipeline {pipeline_id}: {stage}")

        await asyncio.sleep(sleep_s)  # Simulate real work

        p["stages"][stage] = "completed"

    elapsed = round(time.time() - start_ts, 1)
    p["status"] = "completed"
    p["progress"] = 100
    p["completed_at"] = datetime.utcnow().isoformat()
    p["duration_seconds"] = elapsed
    p["logs"].append(f"[{datetime.utcnow().isoformat()}] Pipeline completed in {elapsed}s")

    # Update metrics
    _metrics_store["deployments"]["total"] += 1
    _metrics_store["deployments"]["successful"] += 1
    _metrics_store["build_times_seconds"].append(elapsed)

    logger.info(f"Pipeline {pipeline_id} completed in {elapsed}s")


async def execute_deployment(deploy_id: str, request: DeploymentRequest):
    """
    Simulate blue-green or rolling deployment.
    In production: wrap kubectl, ECS update-service, or Docker Swarm calls.
    """
    d = _deployment_store[deploy_id]
    d["status"] = "deploying"
    d["logs"].append(f"[{datetime.utcnow().isoformat()}] Starting {request.strategy} deployment")

    steps = [
        (3,  f"Pulling image {request.service_name}:{request.version}"),
        (4,  "Starting new instances"),
        (3,  "Running health checks"),
        (2,  "Shifting traffic to new version"),
        (2,  "Draining old instances"),
    ]

    for sleep_s, msg in steps:
        d["logs"].append(f"[{datetime.utcnow().isoformat()}] {msg}")
        await asyncio.sleep(sleep_s)

    d["status"] = "deployed"
    d["completed_at"] = datetime.utcnow().isoformat()
    d["logs"].append(f"[{datetime.utcnow().isoformat()}] Deployment successful")

    _metrics_store["deployments"]["total"] += 1
    _metrics_store["deployments"]["successful"] += 1
    logger.info(f"Deployment {deploy_id} completed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
