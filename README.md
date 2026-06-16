<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1f6feb,100:0d1117&height=200&section=header&text=AI%20DevOps%20Pipeline&fontSize=45&fontColor=58a6ff&fontAlignY=38&desc=Intelligent%20CI%2FCD%20%7C%20Docker%20%7C%20Terraform%20%7C%20GitHub%20Actions&descSize=17&descAlignY=58&descColor=8b949e&animation=fadeIn" />

</div>

<div align="center">

[![CI/CD](https://github.com/codebytaki/ai-devops-pipeline/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/codebytaki/ai-devops-pipeline/actions/workflows/ci-cd.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=flat-square&logo=terraform&logoColor=white)](https://terraform.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/codebytaki/ai-devops-pipeline?style=flat-square&color=yellow)](https://github.com/codebytaki/ai-devops-pipeline/stargazers)
[![Issues](https://img.shields.io/github/issues/codebytaki/ai-devops-pipeline?style=flat-square)](https://github.com/codebytaki/ai-devops-pipeline/issues)

**AI-Powered CI/CD Pipeline with intelligent automation, smart code review, auto-scaling, and real-time monitoring.**

[🚀 Quick Start](#-quick-start) · [✨ Features](#-features) · [🏗️ Architecture](#️-architecture) · [📖 Docs](#-documentation) · [🤝 Contributing](#-contributing)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

**🤖 AI-Powered**
- Intelligent code review on every PR
- AI log analysis & troubleshooting
- Smart resource auto-scaling
- Automated YAML/Dockerfile generation

</td>
<td width="50%">

**⚙️ DevOps Core**
- Full CI/CD with GitHub Actions
- Docker multi-stage builds
- Terraform infrastructure as code
- Blue-green zero-downtime deployments

</td>
</tr>
<tr>
<td width="50%">

**🛡️ Security**
- Automated vulnerability scanning (Trivy, Bandit)
- Secret detection pre-commit
- OWASP dependency checks
- Security gate in pipeline

</td>
<td width="50%">

**📊 Observability**
- Prometheus + Grafana monitoring
- Real-time build/deploy dashboards
- DORA metrics tracking
- Intelligent alerting

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
Developer
    │
    ▼ git push
GitHub Repository
    │
    ▼ Triggers
GitHub Actions CI/CD Pipeline
    ├── 🔍 Lint & Format Check
    ├── 🤖 AI Code Review
    ├── 🧪 Tests (Unit + Integration)
    ├── 🛡️ Security Scan (Trivy + Bandit)
    ├── 🐳 Docker Build & Push
    ├── 🏗️ Terraform Plan/Apply
    └── 🚀 Deploy (Blue-Green)
              │
              ▼
        Production Environment
              │
    ┌─────────┴──────────┐
    │   Prometheus        │
    │   Grafana Dashboard │
    └────────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/codebytaki/ai-devops-pipeline.git
cd ai-devops-pipeline

# 2. Configure
cp .env.example .env
# Edit .env with your API keys and cloud credentials

# 3. Run with Docker Compose
docker compose up -d

# 4. Access dashboards
# App:      http://localhost:5000
# Grafana:  http://localhost:3000
```

> **Prerequisites:** Docker, Docker Compose, Python 3.11+, Git

---

## 📋 Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Core runtime |
| Docker | 24+ | Containerization |
| Terraform | 1.5+ | Infrastructure |
| Git | 2.40+ | Version control |

---

## 🛠️ Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify setup
python src/main.py --check

# Run tests
pytest tests/ -v
```

---

## 💡 Usage

### AI Code Review

```python
from devops_ai import CodeReviewer

reviewer = CodeReviewer(provider="openai")
review = reviewer.analyze_pr(pr_number=42)
print(review.get_suggestions())
```

### AI YAML Generator

```python
from devops_ai import YAMLGenerator

gen = YAMLGenerator()
# Auto-generate GitHub Actions workflow
workflow = gen.github_actions(
    language="python",
    deploy_target="aws-ecs"
)
```

### AI Dockerfile Generator

```python
from devops_ai import DockerfileGenerator

gen = DockerfileGenerator()
dockerfile = gen.generate(
    project_type="fastapi",
    optimize_for="production"
)
```

### Smart Auto-Scaling

```python
from devops_ai import AutoScaler

scaler = AutoScaler(min_instances=2, max_instances=10, target_cpu=70)
scaler.enable()
```

---

## 📁 Project Structure

```
ai-devops-pipeline/
├── .github/
│   ├── workflows/
│   │   └── ci-cd.yml          # Main CI/CD pipeline
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── src/
│   ├── pipeline/              # Pipeline automation
│   ├── ai_engine/             # AI integration modules
│   ├── monitoring/            # Metrics & alerting
│   └── deployment/            # Deployment scripts
├── terraform/
│   ├── main.tf                # AWS infrastructure
│   └── variables.tf
├── monitoring/
│   └── prometheus.yml         # Prometheus config
├── scripts/
│   └── deploy.sh              # Deployment script
├── tests/                     # Test suite
├── docs/                      # Documentation
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CODE_OF_CONDUCT.md
```

---

## 🔧 Configuration

```env
# AI Provider
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here

# Cloud
CLOUD_PROVIDER=aws
AWS_REGION=us-east-1

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/devops_db

# Docker
DOCKER_REGISTRY=docker.io
DOCKER_USERNAME=your_username
```

---

## 📊 Monitoring

Access Grafana at `http://localhost:3000` (default: admin/admin)

**Tracked Metrics (DORA):**
- ✅ Deployment frequency
- ✅ Lead time for changes
- ✅ Mean time to recovery (MTTR)
- ✅ Change failure rate

---

## 🗺️ Roadmap

- [x] Core CI/CD pipeline with GitHub Actions
- [x] Docker + Docker Compose setup
- [x] Terraform AWS infrastructure
- [x] Prometheus + Grafana monitoring
- [ ] 🤖 AI YAML Generator (v1.1)
- [ ] 🐳 AI Dockerfile Optimizer (v1.1)
- [ ] ☁️ AWS Cost Optimizer (v1.2)
- [ ] 🔵 Azure Integration (v1.3)
- [ ] ☸️ Kubernetes Auto-Deploy (v2.0)
- [ ] 🧠 LLM-powered incident response (v2.0)

---

## 🧪 Testing

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Integration only
pytest tests/integration/
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Quick contribution flow
git fork && git clone
git checkout -b feature/your-feature
git commit -m "feat: add your feature"
git push origin feature/your-feature
# Open a Pull Request
```

---

## 🛡️ Security

Found a vulnerability? Please read [SECURITY.md](SECURITY.md) for responsible disclosure guidelines.

---

## 📄 License

MIT © [Taki](https://github.com/codebytaki) — see [LICENSE](LICENSE)

---

<div align="center">

**Built with ❤️ by [codebytaki](https://github.com/codebytaki)**

⭐ Star this repo if it helped you!

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1f6feb,100:0d1117&height=80&section=footer" />

</div>
