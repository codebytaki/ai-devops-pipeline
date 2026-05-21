# 🚀 AI-Powered DevOps Pipeline - Complete Setup Guide

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Setup](#docker-setup)
4. [Cloud Deployment (AWS)](#cloud-deployment-aws)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Monitoring & Logging](#monitoring--logging)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

```bash
# Check versions
python --version  # 3.11+
docker --version  # 20.10+
docker-compose --version  # 2.0+
git --version
terraform --version  # 1.0+ (for cloud deployment)
```

### Required Accounts

- GitHub account (for CI/CD)
- Docker Hub account (for container registry)
- AWS account (for cloud deployment)
- OpenAI API key (for AI features)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/codebytaki/ai-devops-pipeline.git
cd ai-devops-pipeline
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# Required:
# - OPENAI_API_KEY
# - DATABASE_URL
# - AWS credentials (if using AWS)
```

### 5. Run Application Locally

```bash
# Start the application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Access API
# http://localhost:8000
# http://localhost:8000/docs (Swagger UI)
```

---

## Docker Setup

### 1. Build Docker Image

```bash
# Build image
docker build -t ai-devops-pipeline:latest .

# Run container
docker run -p 8000:8000 --env-file .env ai-devops-pipeline:latest
```

### 2. Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services Started:

- **App**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **Jenkins**: http://localhost:8080
- **SonarQube**: http://localhost:9000

---

## Cloud Deployment (AWS)

### 1. Configure AWS Credentials

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

### 2. Initialize Terraform

```bash
cd terraform

# Initialize
terraform init

# Plan deployment
terraform plan

# Apply (deploy)
terraform apply
```

### 3. Deploy Application

```bash
# Build and push Docker image
docker build -t codebytaki/ai-devops-pipeline:v1.0.0 .
docker push codebytaki/ai-devops-pipeline:v1.0.0

# Deploy using script
./scripts/deploy.sh production v1.0.0 blue-green
```

---

## Configuration

### Environment Variables

```env
# AI Configuration
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/devops_db
REDIS_URL=redis://localhost:6379/0

# AWS (for cloud deployment)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# Docker Registry
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password

# Application
APP_ENV=production
LOG_LEVEL=INFO
```

### Terraform Variables

Edit `terraform/terraform.tfvars`:

```hcl
aws_region      = "us-east-1"
environment     = "production"
app_version     = "v1.0.0"
desired_count   = 2
min_capacity    = 2
max_capacity    = 10
```

---

## Running the Application

### Development Mode

```bash
# With auto-reload
uvicorn src.main:app --reload --port 8000
```

### Production Mode

```bash
# Using Docker Compose
docker-compose up -d

# Or using deployment script
./scripts/deploy.sh production latest rolling
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Monitoring & Logging

### Grafana Dashboards

1. Open http://localhost:3000
2. Login: admin/admin
3. Navigate to Dashboards
4. Import pre-configured dashboards

### Prometheus Metrics

- Application metrics: http://localhost:8000/metrics
- Prometheus UI: http://localhost:9090

### Elasticsearch & Kibana

1. Open http://localhost:5601
2. Create index pattern: `logs-*`
3. View logs in Discover tab

### Log Files

```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f app
```

---

## CI/CD Pipeline

### GitHub Actions

Pipeline automatically runs on:
- Push to `main` or `develop` branches
- Pull requests

### Pipeline Stages:

1. **AI Code Review** - Automated PR review
2. **Code Quality** - Linting, security scan
3. **Build & Test** - Unit tests, coverage
4. **Docker Build** - Container image
5. **Security Scan** - Trivy vulnerability scan
6. **Deploy** - Staging/Production deployment

### Manual Trigger

```bash
# Trigger via GitHub UI
# Actions → CI/CD Pipeline → Run workflow
```

### Secrets Required

Add these secrets in GitHub repository settings:

```
OPENAI_API_KEY
DOCKER_USERNAME
DOCKER_PASSWORD
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
SLACK_WEBHOOK_URL (optional)
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process using port
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

#### 2. Docker Build Fails

```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

#### 3. Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

#### 4. Permission Denied (deploy.sh)

```bash
# Make script executable
chmod +x scripts/deploy.sh
```

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Check all services
docker-compose ps

# View resource usage
docker stats
```

### Logs

```bash
# Application logs
docker-compose logs app

# All services logs
docker-compose logs

# Follow logs
docker-compose logs -f app
```

---

## 🎯 Quick Commands Reference

```bash
# Development
uvicorn src.main:app --reload

# Docker
docker-compose up -d
docker-compose down
docker-compose logs -f

# Testing
pytest tests/ -v
pytest tests/ --cov=src

# Deployment
./scripts/deploy.sh production v1.0.0 blue-green

# Terraform
cd terraform
terraform init
terraform plan
terraform apply
terraform destroy

# Monitoring
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus
open http://localhost:5601  # Kibana
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## 🆘 Support

- **Issues**: https://github.com/codebytaki/ai-devops-pipeline/issues
- **Discussions**: https://github.com/codebytaki/ai-devops-pipeline/discussions
- **Email**: support@example.com

---

## 🎉 Success!

Your AI-Powered DevOps Pipeline is now ready!

Access your application:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Monitoring**: http://localhost:3000

Happy DevOps! 🚀
