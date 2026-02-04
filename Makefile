# ================================
# Architect Agent - Makefile
# ================================

.PHONY: help install dev test lint format run docker-up docker-down clean

# Default target
help:
	@echo "Architect Agent - Available commands:"
	@echo ""
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Install with dev dependencies"
	@echo "  make run         - Run the API server"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make docker-up   - Start with Docker Compose"
	@echo "  make docker-down - Stop Docker Compose"
	@echo "  make clean       - Clean build artifacts"
	@echo ""

# Install production dependencies
install:
	pip install -e .

# Install with dev dependencies
dev:
	pip install -e ".[dev]"

# Run the API server
run:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run CLI
cli:
	python -m src.cli

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Lint code
lint:
	ruff check src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	ruff check --fix src/ tests/

# Type checking
types:
	mypy src/

# Docker commands
docker-up:
	docker-compose up -d

docker-up-dev:
	docker-compose --profile dev-tools up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-build:
	docker-compose build --no-cache

# Clean build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .mypy_cache
	rm -rf build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Create .env from example
env:
	cp .env.example .env
	@echo "Created .env - please edit with your credentials"

# Check all
check: lint test
	@echo "All checks passed!"
