# Hedgium Research

Stock analysis service for Hedgium: data ingestion, feature engineering, ML predictions,
risk scoring, and research reports.

## Quick start

```bash
cd hedgium_research
cp .env.example .env
docker compose up -d
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_nifty50
python manage.py runserver 8001
```

Set `ENVIRONMENT=local` in `.env` (default). For Railway use `ENVIRONMENT=dev` or `ENVIRONMENT=prod`.

## Railway deployment

1. Create a new Railway service with **Root Directory** = `hedgium_research`
2. Attach **Postgres** and **Redis** plugins (separate from `hedgium_backend`)
3. Set environment variables:

| Variable | Dev | Prod |
|----------|-----|------|
| `ENVIRONMENT` | `dev` | `prod` |
| `DJANGO_DEBUG` | `False` | `False` |
| `SECRET_KEY` | random secret | random secret |
| `DATABASE_URL` | from Postgres plugin | from Postgres plugin |
| `REDIS_URL` | from Redis plugin | from Redis plugin |
| `RESEARCH_API_KEY` | API key for `X-API-Key` | same |
| `CSRF_TRUSTED_ORIGINS` | `https://<your-dev-domain>.up.railway.app` | prod Railway URL |
| `CORS_ALLOWED_ORIGINS` | Vercel dev + localhost | `https://app.hedgium.ai`, etc. |
| `HEDGIUM_BACKEND_API_URL` | backend API URL | prod backend URL |
| `HEDGIUM_BACKEND_API_KEY` | backend API key | prod key |

4. Deploy — `railway.toml` runs migrations + `collectstatic` on release
5. Procfile starts **web** (gunicorn), **worker**, and **beat** processes (enable worker/beat services in Railway)

Point `hedgium_webapp` at the deployed URL:

```bash
RESEARCH_API_URL=https://<your-research-service>.up.railway.app/api/research/
RESEARCH_API_KEY=<same as research service>
```

One-time after first deploy:

```bash
railway run python manage.py seed_nifty50
```

- Health: `GET /api/research/health/`
- Report: `GET /api/research/TCS/`
- Tasks (admin): `GET /api/research/jobs/`, `POST /api/research/jobs/run/?task_name=...`

In the webapp admin UI: **Research → Jobs** (`/admin/research/tasks`).

## Phase 1 — Data ingestion

Configure Kite credentials **either**:

- `KITE_API_KEY` + `KITE_ACCESS_TOKEN` in `.env`, or
- `HEDGIUM_BACKEND_API_URL` + `HEDGIUM_INTERNAL_SERVICE_TOKEN` (reads market-profile token from backend)

```bash
# Sync Zerodha instrument tokens (no auth required)
python manage.py sync_instrument_tokens

# Backfill OHLCV from Kite (5 years)
python manage.py ingest_ohlcv --backfill-years 5

# Daily incremental OHLCV
python manage.py ingest_ohlcv --days 5

# NSE bhavcopy — delivery % + EOD OHLCV for one date
python manage.py ingest_bhavcopy --date 2024-06-14

# FII/DII flows
python manage.py ingest_fii_dii

# Sector returns (after OHLCV exists)
python manage.py compute_sector_performance

# Corporate actions (last 30 days)
python manage.py ingest_corporate_events

# Full post-market pipeline (Celery task runs this at 6:30 PM IST)
python manage.py run_daily_ingestion
```

## Phase 2 — Feature engineering

```bash
python manage.py compute_features
python manage.py compute_features --ticker TCS
python manage.py import_fundamentals fundamentals.csv
```

## Phase 3 — ML prediction (XGBoost + LightGBM + CatBoost ensemble)

```bash
python manage.py train_prediction_model --model-type all
python manage.py train_prediction_model --model-type lightgbm
python manage.py predict_stocks
python manage.py predict_stocks --ticker TCS
```

Reports use **ensemble-v1** (average of all active models) when multiple models are trained.

## Phase 4 + 5 — AI agents + risk integration

```bash
# Configure provider in .env:
# AGENT_PROVIDER=openai|anthropic
# OPENAI_API_KEY=...
# ANTHROPIC_API_KEY=...

python manage.py runserver 8001
curl http://localhost:8001/api/research/TCS/
```

Response now includes:
- `agent_insights` (technical/fundamental/news/governance/master outputs)
- deterministic `risk_score` + `risk_rules`
- final synthesized `key_positive_factors` and `holding_outlook`

See [AGENTS.md](AGENTS.md) for architecture and conventions.
