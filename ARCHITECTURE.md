# Architecture

## System Overview

```
Developer Workstation
        │
        │ git push
        ▼
┌─────────────────────────────────────────────────────┐
│                GitHub Repository                     │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │          GitHub Actions CI/CD                │   │
│  │                                              │   │
│  │  ① code-quality  ② build-and-test           │   │
│  │       │                  │                  │   │
│  │  flake8/bandit    pytest + coverage          │   │
│  │       │                  │                  │   │
│  │       └────────┬─────────┘                  │   │
│  │                │                            │   │
│  │       ③ docker-build                        │   │
│  │         (Buildx + cache)                    │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
        │
        │ Docker image pushed to registry
        ▼
┌─────────────────────────────────────────────────────┐
│              AWS Infrastructure (Terraform)          │
│                                                     │
│  ┌──────────┐    ┌────────────┐   ┌─────────────┐   │
│  │   ALB    │───▶│ ECS Fargate│   │  Auto Scale │   │
│  │ (Public) │    │  Service   │◀──│  (CPU 70%)  │   │
│  └──────────┘    └─────┬──────┘   └─────────────┘   │
│                        │                            │
│              ┌─────────┴──────────┐                 │
│              │    FastAPI App     │                 │
│              │    (Port 8000)     │                 │
│              └─────────┬──────────┘                 │
│                        │                            │
│         ┌──────────────┼──────────────┐             │
│         ▼              ▼              ▼             │
│    ┌────────┐    ┌──────────┐  ┌──────────────┐     │
│    │  RDS   │    │  Redis   │  │  Secrets Mgr │     │
│    │Postgres│    │  Cache   │  │ (API Keys)   │     │
│    └────────┘    └──────────┘  └──────────────┘     │
│                                                     │
│  ┌──────────────────────────────┐                   │
│  │    Observability Stack       │                   │
│  │  Prometheus ◀── /metrics     │                   │
│  │  Grafana dashboards          │                   │
│  │  CloudWatch Logs             │                   │
│  └──────────────────────────────┘                   │
└─────────────────────────────────────────────────────┘
```

## Module Structure

```
src/
├── main.py                  # FastAPI app, routes, startup
├── pipeline/
│   ├── stages.py            # PipelineStage, StageResult, StageStatus
│   └── runner.py            # PipelineRunner — sequential stage execution
├── ai_engine/
│   ├── reviewer.py          # CodeReviewer (OpenAI / Anthropic / rule-based)
│   └── analyzer.py          # LogAnalyzer — pattern-based log triage
├── deployment/
│   └── strategies.py        # BlueGreenDeployment, RollingDeployment
└── monitoring/
    └── metrics.py           # MetricsCollector — in-process counters
```

## Pipeline Stage Flow

```
queued
  │
  ▼
code_review ──▶ lint ──▶ test ──▶ security_scan ──▶ docker_build ──▶ deploy
                                                                        │
                                                                    completed
                                                                   (or failed)
```

Each stage updates:
- `status`: pending → in_progress → completed | failed | skipped
- `progress`: 0–100%
- `logs`: timestamped entries
- `context`: shared dict passed between stages

## AI Code Review Flow

```
POST /ai/code-review
        │
        ▼
  OPENAI_API_KEY set?
    Yes ──▶ GPT-4o-mini review (JSON output)
    No  ──▶ ANTHROPIC_API_KEY set?
              Yes ──▶ Claude-3-Haiku review
              No  ──▶ Rule-based pattern analysis
        │
        ▼
  { score, suggestions, security_issues, performance_tips }
```

## Deployment Strategy Flow

```
BlueGreenDeployment:
  Pull image → Launch green → Health check → Shift traffic → Drain blue

RollingDeployment:
  Pull image → Replace batch → Health check → Replace remaining → Done
```

## Terraform Infrastructure

```
VPC (10.0.0.0/16)
├── Public Subnets  (ALB, NAT Gateway)
├── Private Subnets (ECS Tasks, RDS)
├── ECS Cluster     (Fargate, Container Insights)
├── ECS Service     (Blue-green circuit breaker, auto-rollback)
├── ALB             (Health checks → /health)
├── Auto Scaling    (Target 70% CPU, min 2 / max 10)
└── Secrets Manager (API keys, DB passwords)
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Optional | Enables real AI code review via GPT-4o-mini |
| `ANTHROPIC_API_KEY` | Optional | Alternative AI provider |
| `DATABASE_URL` | Optional | PostgreSQL connection string |
| `REDIS_URL` | Optional | Redis connection string (default: redis://localhost:6379) |
| `CORS_ORIGINS` | Optional | Comma-separated allowed origins (default: *) |
