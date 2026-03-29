.DEFAULT_GOAL = help

test:  ## Run unit tests
	poetry run pytest

test.exploratory:  ## Run exploratory tests, allowing to fetch real data and save it as tests fixtures
	poetry run pytest -m exploratory

ruff:  ## Lint the codebase
	poetry run ruff check phable

mypy:  ## Check the pytyhon types
	poetry run mypy phable

check_format:  ## Check the codebase formatting
	poetry run ruff format phable --check

lint: ruff mypy check_format  ## Run all linters

ci: lint test  ## Run all checks run in CI

format:  ## Autoformat the codebase
	poetry run ruff format phable

init:  ## Install python dependencies
	poetry install

help:  ## Display help
	@grep -E '^[%a-zA-Z0-9_-\.]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'
