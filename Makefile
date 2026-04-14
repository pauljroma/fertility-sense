.PHONY: test-smoke test-unit test-integration test-property test-e2e test-coverage lint typecheck build docker-build docker-run docker-test install-schedules uninstall-schedules

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

# Docker
docker-build:        ## build Docker image
	docker build -t fertility-sense .

docker-run:          ## run with docker-compose
	docker-compose up

docker-test:         ## run smoke tests inside Docker
	docker run fertility-sense python -m pytest -m smoke

# Scheduling (macOS launchd)
install-schedules:   ## Install launchd schedules (macOS)
	mkdir -p data/logs
	cp deployments/com.winfertility.scout.plist ~/Library/LaunchAgents/
	cp deployments/com.winfertility.digest-daily.plist ~/Library/LaunchAgents/
	cp deployments/com.winfertility.digest-weekly.plist ~/Library/LaunchAgents/
	cp deployments/com.winfertility.sequence-run.plist ~/Library/LaunchAgents/
	launchctl load ~/Library/LaunchAgents/com.winfertility.scout.plist
	launchctl load ~/Library/LaunchAgents/com.winfertility.digest-daily.plist
	launchctl load ~/Library/LaunchAgents/com.winfertility.digest-weekly.plist
	launchctl load ~/Library/LaunchAgents/com.winfertility.sequence-run.plist

uninstall-schedules: ## Remove launchd schedules
	-launchctl unload ~/Library/LaunchAgents/com.winfertility.scout.plist
	-launchctl unload ~/Library/LaunchAgents/com.winfertility.digest-daily.plist
	-launchctl unload ~/Library/LaunchAgents/com.winfertility.digest-weekly.plist
	-launchctl unload ~/Library/LaunchAgents/com.winfertility.sequence-run.plist
	-rm ~/Library/LaunchAgents/com.winfertility.*.plist
