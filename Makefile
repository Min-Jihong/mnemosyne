# =============================================================================
# Mnemosyne Makefile
# =============================================================================
# Common development operations
# Usage: make <target>
# =============================================================================

.PHONY: help install install-dev install-all test lint format typecheck clean build docker run web setup

# Default target
help:
	@echo "Mnemosyne - Your Digital Twin"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Installation:"
	@echo "  install      Install base dependencies"
	@echo "  install-dev  Install with development dependencies"
	@echo "  install-all  Install all optional dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linter (ruff)"
	@echo "  format       Format code (ruff)"
	@echo "  typecheck    Run type checker (mypy)"
	@echo "  check        Run all checks (lint + typecheck + test)"
	@echo ""
	@echo "Running:"
	@echo "  run          Start CLI"
	@echo "  web          Start web interface"
	@echo "  setup        Run setup wizard"
	@echo ""
	@echo "Building:"
	@echo "  build        Build package"
	@echo "  docker       Build Docker image"
	@echo "  clean        Clean build artifacts"

# =============================================================================
# Installation
# =============================================================================

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-web:
	pip install -e ".[web]"

install-macos:
	pip install -e ".[macos]"

install-ml:
	pip install -e ".[ml]"

install-all:
	pip install -e ".[all]"

# =============================================================================
# Development
# =============================================================================

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=mnemosyne --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

test-watch:
	pytest-watch tests/ -- -v

lint:
	ruff check mnemosyne/ tests/

lint-fix:
	ruff check --fix mnemosyne/ tests/

format:
	ruff format mnemosyne/ tests/

format-check:
	ruff format --check mnemosyne/ tests/

typecheck:
	mypy mnemosyne/ --ignore-missing-imports

check: lint typecheck test

# =============================================================================
# Running
# =============================================================================

run:
	python -m mnemosyne

web:
	mnemosyne web --reload

web-prod:
	mnemosyne web --host 0.0.0.0 --port 8000

setup:
	mnemosyne setup

# =============================================================================
# Building
# =============================================================================

build:
	python -m build

build-check:
	twine check dist/*

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# =============================================================================
# Docker
# =============================================================================

docker:
	docker build -t mnemosyne:latest .

docker-dev:
	docker build --target development -t mnemosyne:dev .

docker-run:
	docker run -it --rm -p 8000:8000 -v ~/.mnemosyne:/home/mnemosyne/.mnemosyne mnemosyne:latest

docker-compose-up:
	docker compose up -d

docker-compose-down:
	docker compose down

docker-compose-logs:
	docker compose logs -f

# =============================================================================
# Release
# =============================================================================

release-patch:
	@echo "Bumping patch version..."
	bump2version patch
	git push && git push --tags

release-minor:
	@echo "Bumping minor version..."
	bump2version minor
	git push && git push --tags

release-major:
	@echo "Bumping major version..."
	bump2version major
	git push && git push --tags

# =============================================================================
# Utilities
# =============================================================================

# Generate requirements.txt from pyproject.toml
requirements:
	pip-compile pyproject.toml -o requirements.txt

# Update all dependencies
update:
	pip install --upgrade pip
	pip install -e ".[all]" --upgrade

# Show outdated packages
outdated:
	pip list --outdated

# Create virtual environment
venv:
	python -m venv .venv
	@echo "Activate with: source .venv/bin/activate"
