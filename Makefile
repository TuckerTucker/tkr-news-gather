# Makefile for TKR News Gather
# Updated: 2025-01-04

.PHONY: help install install-dev install-security clean test test-coverage lint format security-scan docker-build docker-run pre-commit setup

# Default target
help:
	@echo "TKR News Gather Development Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup          - Complete development environment setup"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  install-security - Install security scanning tools"
	@echo ""
	@echo "Development Commands:"
	@echo "  test           - Run test suite"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code with black and isort"
	@echo "  pre-commit     - Install and run pre-commit hooks"
	@echo ""
	@echo "Security Commands:"
	@echo "  security-scan  - Run comprehensive security scan"
	@echo "  deps-audit     - Check dependencies for vulnerabilities"
	@echo "  code-audit     - Run static code security analysis"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build   - Build production Docker image (local tag)"
	@echo "  docker-build-hub - Build with Docker Hub username tag"
	@echo "  docker-dev     - Build development Docker image"
	@echo "  docker-run     - Run application in Docker"
	@echo "  docker-compose - Run with docker-compose"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  deploy-runpod  - Interactive RunPod deployment guide"
	@echo "  deploy-quick   - Quick deployment using existing .env config"
	@echo "  deploy-interactive - Alias for deploy-runpod"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  clean          - Clean up temporary files"
	@echo "  clean-all      - Deep clean including dependencies"

# Setup complete development environment
setup: install-dev install-security pre-commit
	@echo "✅ Development environment setup complete!"
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env and add your API keys"
	@echo "  2. Run 'make test' to verify everything works"
	@echo "  3. Run 'make security-scan' to check security"

# Installation targets
install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements-dev.txt

install-security:
	pip install -r requirements-security.txt

# Development targets
test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint:
	flake8 src/ tests/
	mypy src/
	bandit -r src/ -ll

format:
	black src/ tests/
	isort src/ tests/

pre-commit:
	pre-commit install
	pre-commit run --all-files

# Security targets
security-scan:
	@chmod +x scripts/security-scan.sh
	./scripts/security-scan.sh

security-test:
	@chmod +x scripts/test-security.sh
	./scripts/test-security.sh

generate-credentials:
	@chmod +x scripts/generate-credentials.py
	python3 scripts/generate-credentials.py

# New dependency security check
deps-check:
	@chmod +x scripts/deps-check.sh
	./scripts/deps-check.sh

deps-audit:
	safety check
	pip-audit --desc

code-audit:
	bandit -r src/ -ll
	semgrep --config=auto src/

# Poetry-based dependency management
poetry-install:
	poetry install

poetry-update:
	poetry update

poetry-audit:
	poetry run pip-audit
	poetry run safety check
	poetry run bandit -r src/

poetry-export:
	poetry export -f requirements.txt --output requirements-poetry.txt
	poetry export -f requirements.txt --with dev --output requirements-dev-poetry.txt

# Dependency management workflow
deps-update: poetry-update poetry-export deps-check
	@echo "✅ Dependencies updated and security checked!"

security-full: security-scan security-test code-audit deps-check
	@echo "✅ Full security validation completed!"

# Docker targets
docker-build:
	docker build -t tkr-news-gather:latest .

docker-build-hub:
	@if [ -z "$(DOCKER_USERNAME)" ]; then \
		echo "❌ DOCKER_USERNAME environment variable not set"; \
		echo "   Load from .env: export DOCKER_USERNAME=\$$(grep DOCKER_USERNAME .env | cut -d= -f2)"; \
		exit 1; \
	fi
	docker build -t $(DOCKER_USERNAME)/tkr-news-gather:latest .

docker-dev:
	docker build -f Dockerfile.dev -t tkr-news-gather:dev .

docker-run:
	docker run -p 8000:8000 --env-file .env tkr-news-gather:latest

docker-compose:
	docker-compose up --build

# Development server
dev:
	python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run local tests
run-local:
	python run_local.py

# Cleanup targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf reports/

clean-all: clean
	rm -rf .venv/
	pip freeze | grep -v "^-e" | xargs pip uninstall -y

# Quality gates (for CI/CD)
quality-gate: lint test security-scan
	@echo "✅ All quality gates passed!"

# Production readiness check
prod-check: quality-gate
	@echo "🔍 Running production readiness check..."
	python -c "from src.utils import Config; c = Config(); assert c.ANTHROPIC_API_KEY, 'Missing ANTHROPIC_API_KEY'"
	docker build --target production -t tkr-news-gather:prod-test .
	@echo "✅ Production readiness check passed!"

# RunPod deployment
deploy-runpod:
	@echo "🚀 Starting interactive RunPod deployment..."
	python3 deploy.py

deploy-quick:
	@echo "🚀 Starting quick RunPod deployment with existing config..."
	python3 deploy.py --quick

deploy-interactive: deploy-runpod