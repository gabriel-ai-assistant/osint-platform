.PHONY: install test lint typecheck run clean

install:
	pip install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check osint/ tests/
	ruff format --check osint/ tests/

format:
	ruff format osint/ tests/
	ruff check --fix osint/ tests/

typecheck:
	mypy osint/

run:
	osint providers

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
