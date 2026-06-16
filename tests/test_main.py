"""
Tests for AI DevOps Pipeline API
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app, _pipeline_store, _deployment_store, _metrics_store

client = TestClient(app)


# ── Root & Health ─────────────────────────────────────────────────────────────

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0.0"
    assert "docs" in data


def test_health_check_returns_status():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "api" in data["services"]
    assert "uptime_seconds" in data


# ── Pipeline ──────────────────────────────────────────────────────────────────

def test_trigger_pipeline_returns_id():
    payload = {"repo_url": "https://github.com/test/repo", "branch": "main", "environment": "staging"}
    resp = client.post("/pipeline/trigger", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "pipeline_id" in data
    assert data["status"] == "queued"
    assert data["repo"] == payload["repo_url"]
    assert "status_url" in data


def test_trigger_pipeline_missing_repo_fails():
    resp = client.post("/pipeline/trigger", json={"branch": "main"})
    assert resp.status_code == 422  # Pydantic validation error


def test_pipeline_status_not_found():
    resp = client.get("/pipeline/status/nonexistent-id")
    assert resp.status_code == 404


def test_pipeline_status_after_trigger():
    payload = {"repo_url": "https://github.com/test/repo"}
    resp = client.post("/pipeline/trigger", json=payload)
    pid = resp.json()["pipeline_id"]

    status_resp = client.get(f"/pipeline/status/{pid}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["id"] == pid
    assert "stages" in data
    assert "logs" in data


def test_list_pipelines():
    resp = client.get("/pipeline/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "pipelines" in data
    assert "total" in data


# ── AI Code Review ────────────────────────────────────────────────────────────

def test_code_review_rule_based():
    """With no API keys configured, should fall back to rule-based analysis."""
    payload = {"pr_number": 1, "repo_url": "https://github.com/test/repo"}
    resp = client.post("/ai/code-review", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["pr_number"] == 1
    assert data["status"] == "completed"
    assert isinstance(data["suggestions"], list)
    assert isinstance(data["security_issues"], list)
    assert 0 <= data["score"] <= 100


def test_code_review_detects_hardcoded_secret():
    payload = {
        "pr_number": 2,
        "repo_url": "https://github.com/test/repo",
        "diff": 'api_key = "abc123secret"',
    }
    resp = client.post("/ai/code-review", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Rule-based should flag the hardcoded key
    all_issues = data["security_issues"] + data["suggestions"]
    assert len(all_issues) > 0


def test_code_review_score_penalised_for_security_issues():
    payload = {
        "pr_number": 3,
        "repo_url": "https://github.com/test/repo",
        "diff": 'password = "hunter2"\nsecret = "topsecret"',
    }
    resp = client.post("/ai/code-review", json=payload)
    data = resp.json()
    # Multiple security issues should reduce score
    assert data["score"] < 100


# ── Deployment ────────────────────────────────────────────────────────────────

def test_deploy_service_queued():
    payload = {"service_name": "api", "version": "1.2.0", "environment": "staging", "strategy": "blue-green"}
    resp = client.post("/deploy", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "deployment_id" in data
    assert data["status"] == "queued"
    assert data["strategy"] == "blue-green"


def test_deploy_status_not_found():
    resp = client.get("/deploy/status/no-such-deploy")
    assert resp.status_code == 404


def test_deploy_status_after_deploy():
    payload = {"service_name": "worker", "version": "2.0.0", "environment": "production"}
    resp = client.post("/deploy", json=payload)
    did = resp.json()["deployment_id"]

    status_resp = client.get(f"/deploy/status/{did}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["id"] == did
    assert "logs" in data


# ── Metrics & Insights ────────────────────────────────────────────────────────

def test_metrics_structure():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "deployments" in data
    assert "success_rate" in data["deployments"]
    assert "pipelines_tracked" in data


def test_ai_insights_structure():
    resp = client.get("/ai/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert "generated_at" in data
