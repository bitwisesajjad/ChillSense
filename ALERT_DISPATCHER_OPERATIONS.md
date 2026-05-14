# Alert Dispatcher Operations Guide

## Install dependencies

For Docker mode:

- No manual `pip install` is required on host; dependencies are installed during image build from `services/alert_dispatcher/requirements.txt`.

## Run with Docker Compose

In Docker mode, alert-dispatcher connects to the main API via `CHILLSENSE_BASE_URL=http://api:5000` (service-to-service network in compose).
The same connection model is used in both `docker-compose.yml` and `docker-compose.prod.yml`.

### Quick setup for Telegram delivery

**Before running docker compose, add your Telegram bot credentials to a `.env` file in the project root:**

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Then run as usual:

```bash
# 1. Development mode (`docker-compose.yml`)
docker compose up --build

# 2. Production-like mode (`docker-compose.prod.yml`)
docker compose -f docker-compose.prod.yml up --build
```

Useful endpoints in development:

- Alert-dispatcher direct API: `http://localhost:5002/webhooks`
- Deliveries list: `http://localhost:5002/deliveries`
<!-- - One-shot polling: `http://localhost:5002/polling-now` -->
- Swagger UI (only if debug mode is enabled): `http://localhost:5002/apidocs/`

In production-like mode, use NGINX route for one-shot polling:

- Using `http://localhost:5001/dispatcher/` instead of `http://localhost:5002/`

## How service data is created (Webhook + Delivery)

Alert-dispatcher uses SQLite at `services/alert_dispatcher/alert_dispatcher.db`.

When running with Docker Compose, data initialization is automatic when the `alert-dispatcher` container starts (for example after `docker compose up` or container recreate):

- `python3 -m services.alert_dispatcher.init_db`

This creates tables and seeds initial webhook rows.

Seeded webhooks:

- `telegram` (status `0`, active)
- `email` (status `1`, inactive)

### Manual re-seed (optional, only when you want to run init again explicitly):

```bash
# Seeding via container
docker compose exec alert-dispatcher python3 -m services.alert_dispatcher.init_db

# Seeding locally from repo root
source .venv/bin/activate
python3 -m services.alert_dispatcher.init_db
```

### Quick verification:

```bash
curl -s http://localhost:5002/webhooks | python3 -m json.tool
```

You should see at least the `telegram` and `email` rows.

## End-to-end demo flow (required for presentation)

This flow proves that alert-dispatcher receives an unresolved alert and writes delivery logs.

1. Start one compose stack (dev or prod).
2. Trigger an out-of-range reading:

```bash
curl -i -X POST http://localhost:5001/api/shipments/1/readings \
  -H "Content-Type: application/json" \
  -d '{"temp":999,"humidity":40}'
```

3. Trigger one immediate polling cycle (recommended):

```bash
# Development (direct to alert-dispatcher)
curl -i http://localhost:5002/polling-now

# Production-like (through nginx)
curl -i http://localhost:5001/dispatcher/polling-now
```

4. Verify delivery history is updated:

```bash
curl -s http://localhost:5002/deliveries | python3 -m json.tool
```

Expected observation:

- You should see at least one delivery row with the new `alert_id`.
- This confirms alert-dispatcher executed and delivery logging is working.

Note on polling interval:

- In current compose files, `POLL_INTERVAL_SECONDS=600`.
- If you do not call `/polling-now`, wait for the next interval before checking `/deliveries`.

## Run tests (pytest)

```bash
pytest -q tests/services/alert_dispatcher
```

Coverage focused on auxiliary service:

```bash
pytest --cov=services.alert_dispatcher --cov-report=term-missing tests/services/alert_dispatcher -q
```

If import path resolution causes issues:

```bash
PYTHONPATH=. pytest -q tests/services/alert_dispatcher
```

## Verify API/function documentation requirement

### The auxiliary service documents public HTTP methods via OpenAPI/Swagger and internal callable functions via docstrings.

Primary documentation artifacts:

- OpenAPI contract: `services/alert_dispatcher/openapi.yaml`
- HTTP resources code: `services/alert_dispatcher/resources/`
- Internal callable functions: `services/alert_dispatcher/poller/`

### How to verify Swagger/OpenAPI in running service (dev mode):

1. Start the stack in docker development mode.
2. Open `http://localhost:5002/apidocs/` (available when debug mode is enabled).
3. Confirm endpoint contracts for:
  - `GET /webhooks`
  - `PUT /webhooks/{id}`
  - `GET /deliveries`
  - `POST /deliveries`
  - `GET /polling-now`

### How this maps to the required fields:

- Description: the endpoint's `summary` and `description` fields as defined in the OpenAPI contract (`services/alert_dispatcher/openapi.yaml`).
- Input: path params and request body schema/constraints.
- Output: success response schemas (`200`, `201`) and example payload shape.
- Exceptions/failure cases: explicit non-2xx responses (`400`, `404`, `415`, `502`).

If `/apidocs/` is not exposed (for example non-debug mode), reviewers can still validate the same contract directly from `services/alert_dispatcher/openapi.yaml`.