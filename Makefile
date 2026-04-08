.PHONY: test-smoke test-unit test-integration test-property test-e2e test-coverage lint typecheck build

# Test tiers (fast → slow)
test-smoke:          ## <200ms — 5-test heartbeat, pre-commit gate
	python -m pytest -m smoke -q --tb=short --no-header

test-unit:           ## <5s — pure logic, no I/O
	python -m pytest -m unit -q --tb=short --no-header

test-integration:    ## <60s — mocked HTTP, real stores
	python -m pytest -m integration -q --tb=short --no-header

test-property:       ## <2min — Hypothesis edge-case generation
	python -m pytest -m property -q --tb=short --no-header

test-e2e:            ## minutes — full pipeline
	python -m pytest -m e2e -q --tb=short --no-header

test-coverage:       ## full suite with coverage
	python -m pytest --cov=fertility_sense --cov-report=html -q --tb=short

# Quality
lint:                ## ruff lint + format check
	ruff check fertility_sense/ tests/
	ruff format --check fertility_sense/ tests/

typecheck:           ## mypy strict
	mypy fertility_sense/

# Build
build:               ## install in editable mode
	pip install -e ".[feeds,test,dev]" --quiet
