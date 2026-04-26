# Alert Dispatcher Service (Auxiliary)

This service is separated from the main ChillSense API and is responsible for polling unresolved alerts and writing delivery logs.

Main project guide: [README.md](README.md)

## Why this service exists

- Keeps shipment/reading API endpoints focused and responsive.
- Isolates polling and delivery responsibilities from request-response paths.
- Stores webhook and delivery audit data in a dedicated SQLite database.

## Service responsibilities

- Manage webhooks (`GET /webhooks`, `PUT /webhooks/<id>`)
- Store delivery records (`GET /deliveries`, `POST /deliveries`)
- Poll unresolved alerts and create delivery attempts
- Provide demo/manual trigger endpoint (`GET /polling-now`)

## Run with Docker Compose

### 1. Development mode (`docker-compose.yml`)

```bash
docker compose down -v --remove-orphans
docker compose up --build
```

Useful endpoints in development:

- Alert-dispatcher direct API: `http://localhost:5002/webhooks`
- Deliveries list: `http://localhost:5002/deliveries`
- One-shot polling: `http://localhost:5002/polling-now`
- Swagger UI (only if debug mode is enabled): `http://localhost:5002/apidocs/`

### 2. Production-like mode (`docker-compose.prod.yml`)

```bash
docker compose -f docker-compose.prod.yml down -v --remove-orphans
docker compose -f docker-compose.prod.yml up --build
```

In production-like mode, use NGINX route for one-shot polling:

- `http://localhost:5001/dispatcher/polling-now`

## How service data is created (Webhook + Delivery)

Alert-dispatcher uses SQLite at `services/alert_dispatcher/alert_dispatcher.db`.

When running with Docker Compose, data initialization is automatic when the `alert-dispatcher` container starts (for example after `docker compose up` or container recreate):

- `python3 -m services.alert_dispatcher.init_db`

This creates tables and seeds initial webhook rows.

Seeded webhooks:

- `telegram` (status `0`, active)
- `email` (status `1`, inactive)

Manual re-seed (optional, only when you want to run init again explicitly):

```bash
docker compose exec alert-dispatcher python3 -m services.alert_dispatcher.init_db
```

Or locally from repo root:

```bash
source .venv/bin/activate
python3 -m services.alert_dispatcher.init_db
```

Quick verification:

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

From repository root:

```bash
pytest -q tests/services/alert_dispatcher
```

By module:

```bash
pytest -q tests/services/alert_dispatcher/test_app_factory.py
pytest -q tests/services/alert_dispatcher/test_webhooks.py
pytest -q tests/services/alert_dispatcher/test_deliveries.py
pytest -q tests/services/alert_dispatcher/test_polling_now.py
pytest -q tests/services/alert_dispatcher/poller
```

Coverage focused on auxiliary service:

```bash
pytest --cov=services.alert_dispatcher --cov-report=term-missing tests/services/alert_dispatcher -q
```

If import path resolution causes issues:

```bash
PYTHONPATH=. pytest -q tests/services/alert_dispatcher
```

## Local run without Docker (optional)

From repository root:

```bash
source .venv/bin/activate
export CHILLSENSE_BASE_URL=http://localhost:5000
export ALERT_DISPATCHER_BASE_URL=http://localhost:5002
export REQUEST_TIMEOUT_SECONDS=5
export POLL_INTERVAL_SECONDS=15
python3 -m services.alert_dispatcher.init_db
python3 -m services.alert_dispatcher.poller
```

In another shell:

```bash
source .venv/bin/activate
FLASK_DEBUG=1 flask --app services.alert_dispatcher:create_app run --port 5002
```
