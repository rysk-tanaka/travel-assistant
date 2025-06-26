.PHONY: help format lint typecheck test check check-all setup pr clean

# Default target
help:
	@echo "TravelAssistant Development Commands"
	@echo "==================================="
	@echo "make format      - コードフォーマット (ruff)"
	@echo "make lint        - リンター実行 (ruff)"
	@echo "make typecheck   - 型チェック (mypy)"
	@echo "make test        - テスト実行 (pytest)"
	@echo "make check       - format + lint + typecheck + test"
	@echo "make check-all   - pre-commitフック実行"
	@echo "make setup       - 開発環境セットアップ"
	@echo "make pr          - GitHub PR作成"
	@echo "make clean       - キャッシュ削除"

# Code formatting
format:
	uv run ruff format . --config=pyproject.toml

# Linting
lint:
	uv run ruff check . --fix --config=pyproject.toml

# Type checking
typecheck:
	uv run mypy src/ --config-file=pyproject.toml

# Testing
test:
	uv run pytest tests/ -v

# Run all checks
check: format lint typecheck test

# Run pre-commit hooks
check-all:
	uv run pre-commit run --all-files

# Setup development environment
setup:
	@echo "🚀 Setting up TravelAssistant development environment..."
	@echo "Creating virtual environment..."
	uv venv
	@echo "Installing dependencies..."
	uv sync --dev
	@echo "Setting up pre-commit hooks..."
	uv run pre-commit install
	@echo "✅ Setup complete!"

# Create GitHub PR
pr:
	@if [ -z "$(TITLE)" ]; then \
		echo "Error: TITLE is required. Usage: make pr TITLE='PR title' BODY='PR description'"; \
		exit 1; \
	fi
	gh pr create --title "$(TITLE)" --body "$(BODY)" --label "enhancement"

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete