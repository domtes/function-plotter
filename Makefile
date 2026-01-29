all: check test

.PHONY: check
check:
	uvx ty check

.PHONY: test
test:
	uv run pytest
