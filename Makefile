test:
	poetry run pytest -m 'not integration'

ruff:
	poetry run ruff check

mypy:
	poetry run mypy .

check_format:
	poetry run ruff format --check

lint: ruff mypy check_format

ci: lint test

format:
	poetry run ruff format .
