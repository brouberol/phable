test:
	poetry run pytest

ruff:
	poetry run ruff check phable

mypy:
	poetry run mypy phable

check_format:
	poetry run ruff format phable --check

lint: ruff mypy check_format

ci: lint test

format:
	poetry run ruff format phable

init:
	poetry install
