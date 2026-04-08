# Fertility-Sense — Demand-Sensing Intelligence Platform

## What This Is

A nemoclaw-pattern multi-agent system that converts consumer/patient search behavior and investigation behavior into governed product decisions, trusted clinical answers, referrals, and commerce opportunities across the full fertility journey (preconception → postpartum).

## Architecture

Eight domain-specific agents orchestrated via nemoclaw:

| Agent | Role | Tier | Purpose |
|-------|------|------|---------|
| demand-scout | ANALYST | Sonnet | Search trends, social signals, app telemetry |
| evidence-curator | ANALYST | Sonnet | CDC, NIH, FDA evidence ingestion + grading |
| safety-sentinel | ANALYST | Sonnet | FDA alerts, medication/exposure safety |
| ontology-keeper | PLANNER | Opus | Topic graph maintenance + evolution |
| signal-ranker | EXECUTOR | Haiku | Composite TOS scoring |
| answer-assembler | ANALYST | Sonnet | Governed response assembly |
| product-translator | PLANNER | Opus | Signal → product decisions |
| ops-monitor | EXECUTOR | Haiku | Feed health, pipeline monitoring |

## Key Directories

- `agents/` — Agent markdown definitions (YAML frontmatter)
- `cards/` — Agent performance cards (YAML)
- `fertility_sense/` — Python source
- `fertility_sense/models/` — Pydantic data models
- `fertility_sense/feeds/` — 10 data feed implementations
- `fertility_sense/ontology/` — Topic graph + taxonomy
- `fertility_sense/scoring/` — TOS ranking engine
- `fertility_sense/assembly/` — Answer assembly pipeline
- `fertility_sense/governance/` — Trust, safety, escalation
- `fertility_sense/nemoclaw/` — Agent runtime (extends nemo-fleet)
- `data/ontology/` — Canonical taxonomy + aliases (checked in)
- `tests/` — Test suite (smoke/unit/integration/property/e2e)

## Non-Negotiable Rules

1. **Separate demand from evidence.** Never treat social/search chatter as clinical truth.
2. **Every answer must have provenance.** Evidence grade, source, last-reviewed date.
3. **Risk tiers gate publication.** GREEN=auto, YELLOW=evidence-gated, RED=human-review, BLACK=rejected.
4. **No diagnosis, dosage, or emergency triage.** These are disallowed answer classes.
5. **Safety alerts cascade immediately.** When FDA alert fires, all affected answers re-evaluate.

## Branch Discipline

- Never work on main directly
- Feature branches: `git checkout -b <agent-id>/<task>`
- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`

## Test Tiers

```
make test-smoke       # <200ms — 5-test heartbeat, pre-commit gate
make test-unit        # <5s — pure logic, no I/O
make test-integration # <60s — mocked HTTP, real stores
make test-property    # <2min — Hypothesis edge cases
make test-e2e         # minutes — full pipeline
make lint             # ruff check + format
make typecheck        # mypy strict
```

## Scoring Formula

```
TOS = 0.30 * demand + 0.25 * clinical_importance + 0.25 * trust_risk + 0.20 * commercial_fit

Gates:
- trust_risk < 20 → blocked ("unsafe_to_serve")
- clinical_importance > 80 AND trust_risk < 40 → human review
```
