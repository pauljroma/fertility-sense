# Fertility-Sense — Productization Plan

## Current State: Scaffold (86 tests passing, 117 files, 9.4k LOC)
## Target State: Deployable MVP

---

## CRITICAL — Blocks Any Deployment

### C1. Agent Runtime Integration (No Claude API connection)
- [ ] Add `anthropic` SDK to pyproject.toml dependencies
- [ ] Implement ClaudeClient wrapper with cost tracking + rate limiting
- [ ] Load agent system prompts from `agents/*.md` at startup
- [ ] Implement agent dispatcher (skill → agent → Claude call → result)
- [ ] Wire orchestrator phases to real agent execution
- [ ] Add token counting + cost budget enforcement (config has budget, not wired)
- [ ] Decide: use nemo-fleet nemoclaw as pip dependency vs standalone
- **Scope**: orchestrator.py, server.py, new claude_client.py
- **Estimate**: Largest work item

### C2. Security Hardening
- [ ] Add API authentication (Bearer token / API key middleware)
- [ ] Add CORS middleware to FastAPI app
- [ ] Validate all required secrets on startup (fail fast if missing)
- [ ] Pin dependencies — generate `requirements.lock` via pip-compile
- [ ] Add `.env.example` documenting all required env vars
- [ ] Remove empty-string fallbacks for credentials (reddit.py line 106-108)
- **Scope**: api.py, config.py, feeds/reddit.py, new auth middleware

### C3. Deployment Infrastructure
- [ ] Create Dockerfile (multi-stage: build + runtime)
- [ ] Create docker-compose.yml (app + optional postgres)
- [ ] Add graceful shutdown handler to FastAPI
- [ ] Implement real health check aggregation (/health checks feeds + stores)
- [ ] Add readiness/liveness probe endpoints
- **Scope**: new Dockerfile, docker-compose.yml, api.py

### C4. CI/CD Pipeline
- [ ] Create `.github/workflows/test.yml` (smoke + unit on push)
- [ ] Create `.github/workflows/lint.yml` (ruff + mypy on PR)
- [ ] Create `.pre-commit-config.yaml` (ruff, mypy, smoke tests)
- [ ] Add branch protection rules documentation
- **Scope**: new .github/workflows/, .pre-commit-config.yaml

### C5. Configuration Management
- [ ] Refactor FertilitySenseConfig to load from env vars (FERTILITY_SENSE_ prefix)
- [ ] Use python-dotenv (already in deps, unused)
- [ ] Add validation on init (port > 0, budget > 0, etc.)
- [ ] Support per-environment profiles (dev/staging/prod)
- **Scope**: config.py

---

## HIGH — Fix Before Launch

### H1. Async Consistency
- [ ] Make assembly pipeline async (assembler.assemble → async)
- [ ] Make orchestrator phases async (execute_pipeline → async)
- [ ] Add asyncio.wait_for() timeouts on all feed fetches
- [ ] Wire CLI commands to async via asyncio.run()
- **Why**: Feeds are async but rest is sync — blocks I/O on API threads

### H2. Feed Resilience
- [ ] Add retry with exponential backoff (tenacity or manual)
- [ ] Add circuit breaker (after 5 consecutive failures, skip for 5 min)
- [ ] Add per-feed timeout configuration
- [ ] Add jitter to cadence scheduling (avoid thundering herd)
- [ ] Validate credentials on startup, not first fetch
- **Scope**: feeds/base.py, feeds/registry.py

### H3. Observability Stack
- [ ] Replace logging.Formatter with JSON structured logging (structlog)
- [ ] Add request ID correlation (X-Request-ID header → all log lines)
- [ ] Add Prometheus /metrics endpoint (latency histograms, error counters)
- [ ] Instrument: feed ingest time, scoring time, assembly time, governance decisions
- [ ] Wire /feeds/health to real FeedRegistry.health_report()
- **Scope**: log.py, api.py, new metrics.py

### H4. Error Handling Patterns
- [ ] Define structured error types (FeedIngestionError, GovernanceViolationError, etc.)
- [ ] Add proper HTTP error responses in API (not just raw exceptions)
- [ ] Add dead-letter handling for failed feed ingests
- [ ] Add audit logging for all errors (not just governance)
- **Scope**: new errors.py, api.py, feeds/base.py

### H5. Answer Assembly — Replace Placeholders
- [ ] Implement real section composition (currently returns placeholder text)
- [ ] Create system prompts for each template section type
- [ ] Wire answer-assembler agent to Claude for section generation
- [ ] Add safety validation on generated sections before governance gate
- **Scope**: assembly/assembler.py (_compose_section method)

### H6. Disallowed Pattern Enrichment
- [ ] Add more regex patterns (current 5 patterns are easily bypassed)
- [ ] Move patterns to external YAML (not hardcoded)
- [ ] Add optional LLM-based safety check for RED tier queries
- [ ] Add pattern testing framework (examples of what should/shouldn't match)
- **Scope**: governance/disallowed.py

### H7. Stub Feed Implementations
- [ ] Implement CDC ART/NASS feed (critical for IVF success data)
- [ ] Implement FDA Alerts feed (critical for safety-sentinel)
- [ ] Implement NIH/NICHD feed (PubMed API for evidence)
- [ ] Stub remaining 4 can stay for MVP (Search Console, Forum, CDC PRAMS, FDA PLLR)
- **Scope**: feeds/cdc_art_nass.py, fda_alerts.py, nih_nichd.py

---

## MEDIUM — Tech Debt (Post-MVP)

### M1. Database Migration
- [ ] Add SQLAlchemy models + Alembic migrations
- [ ] Migrate file-backed stores to PostgreSQL
- [ ] Add connection pooling
- [ ] Add concurrent write safety (file stores have no locking)
- [ ] Add data retention policies
- **Why**: File stores work but corrupt under concurrent load

### M2. Risk Classifier Improvements
- [ ] Move RED_KEYWORDS / BLACK_KEYWORDS to config YAML
- [ ] Add feedback loop to update keywords from governance audit data
- [ ] Add fuzzy matching to alias resolver (rapidfuzz)
- **Scope**: assembly/risk_classifier.py, ontology/resolver.py

### M3. Signal Deduplication
- [ ] Add cross-feed dedup in FeedRegistry (same topic from multiple sources)
- [ ] Prevent TOS double-counting demand
- **Scope**: feeds/registry.py

### M4. Scoring Flexibility
- [ ] Allow per-topic weight overrides in TopicNode
- [ ] Make evidence recency horizon configurable per source
- [ ] Add A/B test harness for weight schemes
- **Scope**: scoring/composite.py, config.py

### M5. Taxonomy Versioning
- [ ] Add version field to taxonomy.yaml
- [ ] Track historical versions in data/ontology/versions/
- [ ] Add taxonomy diff/audit tool
- **Scope**: data/ontology/, ontology/taxonomy.py

---

## LOW — Nice to Have

- [ ] CLI: wire all commands to real orchestrator + add --json output
- [ ] Search: add trigram/BM25 index for topic search at scale
- [ ] ContentBrief: LLM-generated angles instead of template strings
- [ ] Feed rate limiting: add semaphore for concurrent feed tasks
- [ ] Data model: add answer_version, confidence_interval on TOS
- [ ] Template: add CONSULT intent type, dynamic template generation

---

## Priority Order (Implementation Sequence)

```
Week 1-2:  C2 (security) + C4 (CI/CD) + C5 (config) + H2 (feed resilience)
Week 3-4:  C1 (agent runtime — start) + H1 (async) + H3 (observability)
Week 5-6:  C1 (agent runtime — complete) + H5 (answer assembly) + H7 (feeds)
Week 7:    C3 (deployment) + H4 (error handling) + H6 (disallowed patterns)
Week 8:    Integration testing + staging deployment + smoke validation
```

## Done
- [x] Repository scaffold (configs, directories, git init)
- [x] Pydantic data models (9 files)
- [x] Topic ontology (91 topics, 262 aliases, graph + resolver)
- [x] Feed infrastructure (base + registry + 3 MVP + 7 stubs)
- [x] Scoring engine (4 sub-scores + composite TOS)
- [x] Assembly pipeline + governance (5-stage + escalation matrix)
- [x] Agent runtime skeleton (8 agents, 30+ skills, orchestrator)
- [x] API + CLI + product layer
- [x] 86 tests passing (smoke, unit, e2e)
