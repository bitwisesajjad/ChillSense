# Alert Dispatcher Service (Auxiliary)

This is a minimal alert-dispatcher service for managing webhooks and delivery logs, designed to be simple and easy to run alongside the main ChillSense app.

## Features
- Manage webhooks (active/inactive)
- Log alert deliveries to webhooks
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

At container startup, the service runs `python3 -m services.alert_dispatcher.init_db`
to create the SQLite database file and seed webhook rows automatically.

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
