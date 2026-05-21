"""
Tests for main application
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["version"] == "1.0.0"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data


def test_trigger_pipeline():
    """Test pipeline trigger"""
    payload = {
        "repo_url": "https://github.com/test/repo",
        "branch": "main",
        "environment": "production",
        "auto_deploy": False
    }
    response = client.post("/pipeline/trigger", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pipeline_triggered"
    assert data["repo"] == payload["repo_url"]


def test_ai_code_review():
    """Test AI code review"""
    payload = {
        "pr_number": 42,
        "repo_url": "https://github.com/test/repo",
        "ai_provider": "openai"
    }
    response = client.post("/ai/code-review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["pr_number"] == 42
    assert data["status"] == "completed"
    assert "suggestions" in data


def test_deploy_service():
    """Test service deployment"""
    payload = {
        "service_name": "test-service",
        "version": "1.0.0",
        "environment": "staging",
        "strategy": "blue-green"
    }
    response = client.post("/deploy", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deployment_initiated"
    assert data["service"] == payload["service_name"]


def test_pipeline_status():
    """Test pipeline status"""
    response = client.get("/pipeline/status/test-123")
    assert response.status_code == 200
    data = response.json()
    assert "pipeline_id" in data
    assert "status" in data
    assert "stages" in data


def test_metrics():
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "deployments" in data
    assert "build_time" in data
    assert "code_quality" in data


def test_ai_insights():
    """Test AI insights"""
    response = client.get("/ai/insights")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "predictions" in data
    assert "trends" in data


@pytest.mark.asyncio
async def test_invalid_pipeline_request():
    """Test invalid pipeline request"""
    payload = {
        "repo_url": "",  # Invalid empty URL
        "branch": "main"
    }
    response = client.post("/pipeline/trigger", json=payload)
    # Should handle validation
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_code_review_with_invalid_pr():
    """Test code review with invalid PR number"""
    payload = {
        "pr_number": -1,  # Invalid PR number
        "repo_url": "https://github.com/test/repo"
    }
    response = client.post("/ai/code-review", json=payload)
    # Should handle validation
    assert response.status_code in [200, 422]
