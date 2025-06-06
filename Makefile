.PHONY: help init sync install test test-unit test-integration test-all coverage lint lint-check format ci-lint run run-server run-local docker-build docker-run clean

help:
	@echo "Available commands:"
	@echo "  make init               - Initialize Rye project"
	@echo "  make sync               - Sync dependencies with Rye"
	@echo "  make install            - Install dependencies (alias for sync)"
	@echo "  make test               - Run provider unit tests"
	@echo "  make test-unit          - Run provider unit tests"
	@echo "  make test-integration   - Run integration tests (requires longer time)"
	@echo "  make test-all           - Run all tests (provider + integration)"
	@echo "  make coverage           - Run tests with coverage report"
	@echo "  make lint               - Run linting (flake8 + mypy)"
	@echo "  make lint-check         - Check code formatting (black + isort)"
	@echo "  make format             - Format code (black + isort)"
	@echo "  make ci-lint            - Run all linting checks (for CI)"
	@echo "  make run                - Run the LiteLLM proxy server"
	@echo "  make run-server         - Run the LiteLLM proxy server (alias for run)"
	@echo "  make run-local          - Run the server using run_local.sh script"
	@echo "  make docker-build       - Build Docker image"
	@echo "  make docker-run         - Run Docker container"
	@echo "  make docker-claude-login - Login to Claude in Docker container"
	@echo "  make docker-down        - Stop Docker containers"
	@echo "  make clean              - Clean up generated files"

init:
	rye init

install: sync

sync:
	rye sync



lint:
	rye run flake8 claude_code_server
	rye run mypy claude_code_server

lint-check:
	rye run black --check claude_code_server
	rye run isort --check-only claude_code_server

format:
	rye run black claude_code_server tests
	rye run isort claude_code_server tests

ci-lint: lint lint-check

test:
	rye run pytest tests/test_provider.py -v

test-integration:
	rye run pytest tests/test_integration.py -m integration -v

test-all:
	rye run pytest -v

coverage:
	rye run pytest --cov=claude_code_server --cov-report=html --cov-report=term

run:
	LITELLM_LOG=debug rye run litellm --config litellm_config.yaml



docker-build:
	@echo "Generating requirements.txt from requirements.lock..."
	@grep -v "^#" requirements.lock | grep -v "^-e file:\." | grep -v "^[[:space:]]*#" | grep -v "^$$" > requirements.txt
	@echo "Building Docker image..."
	docker build -t claude-code-server:latest .
	@echo "Cleaning up requirements.txt..."
	@rm -f requirements.txt

docker-run:
	docker compose up -d

docker-claude-login:
	docker compose exec claude-code-server claude /login

docker-down:
	docker compose down


clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov .pytest_cache
	rm -rf build dist *.egg-info