# Contributing to AI DevOps Pipeline

Thank you for your interest in contributing! 🎉

## Ways to Contribute

- 🐛 Bug reports
- ✨ Feature requests
- 📖 Documentation improvements
- 🔧 Code contributions
- 🧪 Tests

## Getting Started

### 1. Fork & Clone

```bash
git fork https://github.com/codebytaki/ai-devops-pipeline
git clone https://github.com/YOUR_USERNAME/ai-devops-pipeline
cd ai-devops-pipeline
```

### 2. Set Up Environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # dev dependencies
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 4. Make Changes

- Follow existing code style
- Add/update tests for your changes
- Update docs if needed

### 5. Test

```bash
pytest tests/ -v
pytest tests/ --cov=src
```

### 6. Commit

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add AI Dockerfile generator"
git commit -m "fix: resolve Docker build cache issue"
git commit -m "docs: update installation guide"
```

### 7. Push & Open PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

## Code Standards

- PEP 8 for Python
- Type hints where possible
- Docstrings for public functions
- No hardcoded secrets (use `.env`)

## Pull Request Guidelines

- Describe what and why in the PR description
- Link related issues (`Closes #123`)
- Keep PRs focused — one feature/fix per PR
- Ensure CI passes before requesting review

## Need Help?

Open a [Discussion](https://github.com/codebytaki/ai-devops-pipeline/discussions) or [Issue](https://github.com/codebytaki/ai-devops-pipeline/issues).
