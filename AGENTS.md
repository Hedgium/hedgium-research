# AGENTS.md — Hedgium Research

AI agent context for the `hedgium_research` Django project.
Read this before touching any code.

---

## Project Identity

**Hedgium Research** is a stock analysis service: market data ingestion, pre-computed
features, ML predictions (XGBoost), rule-based risk scoring, LLM agent synthesis,
and user-facing research reports.

It is **separate from** `hedgium_backend` trading execution. Never place orders or
mutate trade state from this project.

---

## Stack

| Layer | Technology |
|-------|------------|
| Framework | Django 5.2 |
| API | Django Ninja Extra |
| Background tasks | Celery + Redis |
| Database | Dedicated Postgres (`DATABASE_URL`) — not the trading DB |
| Cache | Redis (optional locally) |
| Time zone | `Asia/Kolkata` |

---

## Project Structure

```
hedgium_research/
├── config/           # Settings, URLs, Celery
├── symbols/          # Companies, symbols, NIFTY 50 seed
├── market_data/      # OHLCV, delivery, FII/DII, events, news
├── features/         # Pre-computed feature snapshots
├── analysis/         # Predictions, risk, reports, API
└── jobs/             # Celery tasks (ingestion, features)
```

---

## Conventions

- **Business logic in `services.py`** (or `services/` package), not views/API handlers.
- **Features are pre-computed** — never calculate RSI/MACD inside LLM prompts.
- **Predictions use ML** (XGBoost) — never use LLM for price forecasting.
- **Risk warnings are rule-based** — auditable, deterministic.
- **LLM agents** (future) interpret structured data only.

---

## Local development

```bash
cd hedgium_research
cp .env.example .env
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_nifty50
python manage.py runserver 8001
```

`ENVIRONMENT=local` (default) loads `config.settings_local`. Railway uses `ENVIRONMENT=dev` or `prod`.

API: `GET http://localhost:8001/api/research/health/`
Report: `GET http://localhost:8001/api/research/TCS/`

Celery (with Redis running):

```bash
celery -A config worker -l info
celery -A config beat -l info
```

---

## Phase 2 — Feature engineering

Pre-computed snapshots stored in `FeatureSnapshot` (never computed in LLM layer).

```bash
python manage.py compute_features              # NIFTY 50 universe
python manage.py compute_features --ticker TCS
python manage.py import_fundamentals data.csv  # optional PE/PB/ROE rows
```

Feature groups: `TECHNICAL`, `VOLATILITY`, `FUNDAMENTAL`, `CORPORATE_RISK`.

Celery runs `compute_features_daily` at 7:00 PM IST after ingestion.

## Phase 3 — ML prediction (XGBoost + LightGBM + CatBoost)

30-day direction classifier with **ensemble** averaging (no LLM).

```bash
python manage.py train_prediction_model --model-type all
python manage.py predict_stocks --ticker TCS
```

## Phase 4+5 — LLM interpretation + risk integration

- Agents are interpretation-only. They must never compute indicators or override ML probabilities.
- Deterministic risk engine owns `risk_level` and `risk_score`.
- Multi-provider LLM support:
  - `AGENT_PROVIDER=openai|anthropic`
  - `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
- If provider fails or is disabled, use deterministic fallback summaries.

## Integration with hedgium_backend

- **Read-only** use of backend market APIs for live quotes / instrument tokens.
- **Separate database** — sync symbols via management commands or internal API.
- Do not add research tables to `hedgium_backend` migrations.
