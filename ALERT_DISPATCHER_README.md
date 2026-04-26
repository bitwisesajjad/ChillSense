# Alert Dispatcher Service (Auxiliary)

This is a minimal alert-dispatcher service for managing webhooks and delivery logs, designed to be simple and easy to run alongside the main ChillSense app.

## Why this auxiliary service is necessary
- This service separates alert dispatching from the core ChillSense API responsibilities.
- It handles polling, delivery attempts, and delivery logging as background work.
- Keeping these tasks outside the main API helps keep shipment/reading endpoints responsive.

## Why direct implementation in ChillSense API is problematic
- Alert delivery is slow and unpredictable (network calls, retries, temporary failures).
- If done directly in API request handlers, user-facing endpoints can become slower or unstable.
- Dispatch logic needs independent operation and recovery (continuous polling loop, rollback on errors).
- Delivery audit data (webhooks and delivery history) is operational data and is cleaner in a separate service boundary.

## Features
- Manage webhooks (active/inactive)
- Log alert deliveries to webhooks
- Continuous polling worker for fetching alerts and dispatching webhook deliveries
- SQLite database, no migrations, no over-engineering

## Run with Docker Compose

The service is now included as `alert-dispatcher` in `docker-compose.yml`.

1. Start the stack:

```bash
docker compose up --build
```

2. Access the service:

- API: `http://localhost:5002/webhooks`
- Swagger UI: `http://localhost:5002/apidocs/`

3. Poller worker:

- Runs inside the same `alert-dispatcher` container
- Calls `services.alert_dispatcher.poller.dispatcher.poll_and_dispatch_alerts()` continuously
- Poll interval is controlled by `POLL_INTERVAL_SECONDS` (default `15`)

4. Demo-only manual trigger endpoint:

- `GET /polling-now` is provided only for demo/manual trigger scenarios.
- This endpoint runs exactly one poll-and-dispatch cycle immediately.
- Do not use this endpoint as a scheduler replacement in normal production flow.
- Example (direct service): `curl -i http://localhost:5002/polling-now`
- Example (through nginx prod proxy): `curl -i http://localhost:5001/dispatcher/polling-now`

At container startup, the service runs `python3 -m services.alert_dispatcher.init_db`
to create the SQLite database file and seed webhook rows automatically.

At container startup, the command initializes DB and then starts both:

- Flask API (`:5002`)
- Poller loop (background process)

## Run poller locally (without Docker)

From repository root:

```bash
source .venv/bin/activate
export CHILLSENSE_BASE_URL=http://localhost:5000
export REQUEST_TIMEOUT_SECONDS=5
export POLL_INTERVAL_SECONDS=15
python3 -m services.alert_dispatcher.init_db
python3 -m services.alert_dispatcher.poller
```

## How to initialize and seed the database

1. **Install dependencies** (if not already):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Initialize the database** (creates `services/alert_dispatcher/alert_dispatcher.db` and seeds 2 webhooks):

```bash
python3 -m services.alert_dispatcher.init_db
```

- This will create the tables `Webhook` and `Delivery` in a local SQLite file.
- It will also insert 2 sample webhooks:
  - `telegram` (active)
  - `email` (inactive)

3. **Verify the database** (optional):

```bash
python3 -c "import sqlite3; print(list(sqlite3.connect('services/alert_dispatcher/alert_dispatcher.db').execute('SELECT * FROM Webhook')),)"
```

## Data handling rules
- No delete operation is allowed for either table.
- Webhooks can only change status (active/inactive).
- Deliveries can only be inserted (no update/delete).

## Notes
- Uses local SQLite for service data (`services/alert_dispatcher/alert_dispatcher.db`).
- You can safely re-run the init script; it will not duplicate webhooks.
- For integration, import and use the models in `services/alert_dispatcher/models.py`.

---

For more details, see the main README or the code in `services/alert_dispatcher/`.
