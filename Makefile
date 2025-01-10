.PHONY: check
check: lint test

.PHONY: lint
lint:
	uv run ruff format src/
	uv run ruff check --fix --show-fixes src/
	uv run mypy src/

.PHONY: test
test:
	uv run pytest src/

.PHONY: api
api:
	uv run uvicorn cloudflare_dyndns.api:app --reload