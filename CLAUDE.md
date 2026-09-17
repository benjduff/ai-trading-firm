# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This is an early-stage scaffold, not yet a mature codebase:

- The repo root itself is not a git repository. `apps/web` has its own independent `.git` (created by `create-next-app`), and `apps/api` has no git repo at all.
- `apps/web` is an unmodified Next.js starter (from `create-next-app`) — `app/page.tsx` still has the default template content.
- `apps/api` is a minimal FastAPI skeleton with a single `/health` endpoint and no other routes, tests, or business logic yet.
- There is no top-level build system tying the two apps together (no root package.json, no Makefile, no CI config).

When making structural decisions (adding a monorepo tool, initializing root git, wiring up CI), confirm with the user rather than assuming — this repo hasn't committed to a shape yet.

## apps/web (Next.js frontend)

Standard Next.js 16 app using the App Router, TypeScript, Tailwind CSS v4, and React 19 with the React Compiler enabled (`reactCompiler: true` in `next.config.ts`).

Commands (run from `apps/web`):
```bash
npm run dev      # start dev server on localhost:3000
npm run build    # production build
npm run start    # serve production build
npm run lint     # eslint (flat config via eslint.config.mjs)
```

No test runner is configured yet.

Note: `AGENTS.md` in this directory is auto-generated/re-added by `next dev` itself (see `node_modules/next/dist/server/lib/generate-agent-files.js`) and documents that this Next.js version may differ from an LLM's training data — check `node_modules/next/dist/docs/` for version-specific API/convention changes before writing Next.js code here.

## apps/api (FastAPI backend)

Python backend managed with `uv` (see `uv.lock`), targeting Python >=3.9, using FastAPI with the `standard` extras group and `pydantic-settings`.

Commands (run from `apps/api`):
```bash
uv sync                              # install dependencies into .venv
uv run fastapi dev app/main.py       # run dev server with reload
uv run fastapi run app/main.py       # run production server
```

The app entrypoint is `app.main:app` (also declared under `[tool.fastapi]` in `pyproject.toml`). There are no tests configured yet.

## Project

A human-in-the-loop AI trading research firm. The AI finds opportunities, researches
companies, analyzes fundamentals/quant/psychology, red-teams its own thesis, assesses
risk, and produces structured trade proposals. **A human always makes the final
call.** The AI never autonomously executes a trade.

Initial strategy scope: liquid US equities, event/catalyst-driven, holding periods of
days to weeks, fundamental + quant + psychology analysis, every trade human-approved.
This is *not* starting as HFT, an autonomous bot, a chart-reading LLM, a pure
technical strategy, or anything managing outside capital.

## Non-negotiable rules

- **No autonomous execution, ever.** The AI produces an Order Proposal; a human
  approves it; only then can a separate execution component place an order. Never
  implement a code path where an agent or pipeline can send an order directly. A
  system-prompt instruction not to trade is not a substitute for this architectural
  separation — enforce it in code/service boundaries.
- **LLMs interpret; deterministic Python calculates.** Returns, volatility,
  correlations, beta, position sizing, risk limits, order validation, and all other
  arithmetic/risk-control logic must be deterministic Python, never delegated to an
  LLM. LLMs read filings, transcripts, and narratives, and reason about them.
- **Don't trust LLM self-reported confidence** (e.g. "87% confident"). Confidence
  should eventually be derived empirically from historical outcomes, not model output.
- **Point-in-time integrity.** Every piece of evidence needs publication timestamp,
  ingestion timestamp, source, document hash, and (once agents exist) model/prompt
  version. This prevents look-ahead bias in later backtesting.
- **Model-provider agnostic.** Don't hard-code a single AI provider into the trading
  logic. Design for a model gateway (OpenAI, Anthropic, Google, xAI, Perplexity,
  self-hosted) even if only one provider is wired up today.
- **Red Team independence.** When it exists, the Bear/Red-Team analyst should not see
  the primary analyst's thesis before forming its own view, and should ideally run on
  a different model/provider.
- **Structured output only.** Agent outputs must be validated Pydantic models, not
  free-form text treated as the application's internal data model.

## Tech stack

- **Frontend:** Next.js, TypeScript, App Router, Tailwind — `apps/web`
- **Backend:** Python, FastAPI, Pydantic, `uv` — `apps/api` (later: SQLAlchemy, Alembic)
- **Database:** PostgreSQL (not yet wired up)
- **Quant/analytics:** Python, Pandas/Polars, Parquet, DuckDB (later)
- **Backend dev server:** `uv run fastapi dev`

Mental model: **Next.js = control room, Python = research/quant brain, Postgres =
institutional memory.**

## Target repo structure

```
ai-trading-firm/
├── apps/
│   ├── web/            # Next.js frontend
│   └── api/             # FastAPI backend
├── agents/
│   ├── fundamental/
│   ├── psychology/
│   ├── red_team/
│   ├── risk/
│   ├── cio/
│   └── scout/
├── research/
│   ├── sec/
│   ├── transcripts/
│   ├── news/
│   └── retrieval/
├── quant/
│   ├── market_data.py
│   ├── event_study.py
│   ├── valuation.py
│   ├── portfolio.py
│   └── risk_metrics.py
├── execution/
│   ├── proposals.py
│   └── broker_ibkr.py
├── schemas/
│   ├── evidence.py
│   ├── thesis.py
│   ├── psychology.py
│   └── trade_proposal.py
├── evaluation/
│   ├── outcomes.py
│   ├── model_comparison.py
│   └── calibration.py
├── docker-compose.yml
├── .env.example
└── INVESTMENT_POLICY.md
```

This can evolve — don't over-engineer package boundaries before the first vertical
slice works.

## Current state

- Repo created. `apps/web` scaffolded (standard Next.js). `apps/api` started, `uv`
  installed. No meaningful application logic yet.
- No Postgres, no AI agents, no evidence ingestion yet — all still to come.

## What to build right now (do not skip ahead)

We're building **one vertical slice at a time**, in this order:

ticker input → research job → evidence → one agent → multiple independent agents →
trade proposal → human decision → outcome tracking → paper execution → (eventually)
live trading.

### Immediate task: first working vertical slice (Phase 1)

1. Verify the FastAPI service starts.
2. Implement `GET /health` → `{"status": "ok", "service": "ai-trading-firm-api"}`.
3. Define a `ResearchJob` Pydantic model (`id`, `ticker`, `created_at`, `status`,
   `as_of`, `requested_by`).
4. Define `CreateResearchRequest` containing a `ticker`.
5. Implement `POST /research` — generate a UUID, normalize ticker to uppercase, store
   in memory (no DB yet).
6. Add `GET /research/{id}`.
7. In Next.js, build a minimal page: ticker input → "Investigate" button → POST to
   FastAPI → display returned job ID and status.
8. Add basic validation/error handling (invalid/empty ticker → sensible error).

**Acceptance criteria:** both apps run locally; entering "oxy" in the frontend results
in a stored job with ticker `"OXY"`; the frontend displays the job's ID and status;
`GET /research/{id}` returns the same job; invalid/empty tickers are rejected
cleanly.

**Do not add Postgres or AI in this task.**

### After that, in order

- **Phase 2 — Core schemas:** `ResearchJob`, `Evidence`, `AgentReport`,
  `PsychologyReport`, `TradeProposal`, `HumanDecision`. Keep them simple; they'll
  evolve.
- **Phase 3 — PostgreSQL:** Docker Compose, SQLAlchemy, Alembic, persist
  `ResearchJob`s. Don't design a large schema up front.
- **Phase 4 — Evidence ingestion:** SEC EDGAR first (ticker → CIK → filings → stored
  Evidence with timestamps). Start with 10-K/10-Q/8-K.
- **Phase 5 — First agent:** Fundamental Analyst only. Structured Evidence in,
  validated `FundamentalReport` out. Don't build six agents at once.
- **Phase 6 — Psychology Agent:** forms its view independently of the Fundamental
  Analyst's conclusion before either sees the other, to reduce confirmation bias. See
  "Market Psychology" below for the concepts it should track.
- **Phase 7 — Red Team:** challenges the Fundamental thesis, ideally on a different
  model/provider, without seeing it first.
- **Phase 8 — Quant service:** deterministic Python for returns, abnormal returns,
  volatility, volume, beta, correlations, drawdowns, sector-relative behavior. Never
  LLM-calculated.
- **Phase 9 — CIO Synthesizer:** combines Fundamental + Psychology + Red Team + Quant
  + Risk into one structured `TradeProposal`. It synthesizes; it does not do new
  research.
- **Phase 10 — Human decision UI:** dashboard showing thesis, catalyst, expectation
  gap, psychology, red-team findings, quant, risk, uncertainties, invalidation
  conditions, evidence links. Actions: Approve / Reject / Watch / Request More
  Research. Store the human's reasoning — it's valuable proprietary data.
- **Phase 11 — Forward shadow portfolio:** freeze every proposal against live
  outcomes, including rejected ones, before any real/paper execution exists.
- **Phase 12 — Paper trading:** Interactive Brokers paper account, execution service
  kept separate from the research system, explicit human approval required, hard risk
  rules in place. No autonomous execution.

## Market Psychology agent — concepts to model

Answers: *what does the market already believe, how strongly, and what's priced in?*
Central concept is the **expectation gap** = our forward view − implied market view.
Extreme sentiment is not itself a timing signal; don't auto-generate contrarian
trades from it.

Roughly track: `market_temperature` (-5 panic … 0 neutral … +5 euphoria),
`expectation_gap`, `fear_of_loss`, `fomo`, `narrative_saturation`, `crowding`,
`dominant_narrative`, `differentiated_or_contrarian_view`, `psychology_confidence`,
`evidence`, `previous_state_id`. Store historically so psychology shifts over time
can be analyzed later.

## Evidence model

Every material claim should trace as: `claim → source → timestamp → extracted
evidence`. Prefer primary sources: SEC EDGAR, company IR sites, earnings releases and
transcripts, FRED/ALFRED, market price data, news APIs.

## Explicitly out of scope for now

Don't build any of these until the research pipeline above is proven out:
complex auth, multi-user support, mobile apps, elaborate charting, microservices,
Kubernetes, dozens of agents, full market scanning, ML models, autonomous execution,
portfolio optimization, institutional data subscriptions, historical LLM
backtesting, heavy vector infra, full broker integration.

## Working style

- Build vertical slices; don't build the whole architecture before anything runs.
- Prefer simple, evolvable schemas over "perfect" upfront design.
- Every layer should remain testable and auditable — this system's long-term value is
  the accumulated evidence, theses, psychology states, model outputs, human
  decisions, and outcomes it preserves, not the UI. Don't lose or discard that data
  when iterating.
