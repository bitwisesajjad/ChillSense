# PWP SPRING 2026

# PROJECT NAME: ChillSense

## Group information

- Student 1. Sajjad Ghaeminejad (sghaemin25@student.oulu.fi)
- Student 2. Hieu Nguyen (hieu.nguyen@student.oulu.fi)

**Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment**

## How to use

### 1. Run with Docker Compose (recommended)

#### 1.1. Development mode (`docker-compose.yml`)

```bash
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up
```

Entrypoints in development mode:

- Main API: `http://localhost:5001/api/shipments`
- Main API Swagger: `http://localhost:5001/apidocs/`
- Alert-dispatcher API (direct): `http://localhost:5002/webhooks`
- Alert-dispatcher Swagger (direct, only when debug mode is enabled): `http://localhost:5002/apidocs/`
- Client UI (static server): `http://localhost:5003/`

#### 1.2. Production-like mode (`docker-compose.prod.yml`)

```bash
docker compose -f docker-compose.prod.yml down -v --remove-orphans
docker compose -f docker-compose.prod.yml up --build
```

Entrypoints in production-like mode (served by NGINX):

- Main API: `http://localhost:5001/api/shipments`
- Alert-dispatcher trigger endpoint via NGINX: `http://localhost:5001/dispatcher/polling-now`
- Client UI: `http://localhost:5001/`

#### 1.3. Why two Docker modes?

- Development mode keeps fast iteration and current workflow (live code updates, debug enabled).
- Production mode uses a proper web-server/app-server chain:
  - NGINX handles public HTTP traffic and reverse-proxy routing.
  - Gunicorn runs the Flask WSGI app with worker processes.

#### 1.4. Monitor and control checks

Use these commands after starting production mode:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
docker inspect <container_name> --format='{{.State.Health.Status}}'
```

Notes:

- `ps` shows service state and health status.
- `logs -f api` follows Gunicorn/API logs in real time.
- `docker inspect` confirms health state (`starting`, `healthy`, or `unhealthy`) for each container.

#### 1.5. Auxiliary service justification (Alert Dispatcher)

- We implemented `services/alert_dispatcher` as a separate auxiliary service.
- It polls unresolved alerts from ChillSense API and dispatches them to configured webhooks.
- This is intentionally outside the main API server to avoid mixing core REST operations with long-running background jobs.

Why not do this directly inside ChillSense API:

- Webhook delivery depends on external networks and can be slow/fail intermittently.
- Running dispatch logic inside request-response endpoints can increase latency and reduce API reliability.
- A separate service provides cleaner isolation, independent restart behavior, and independent delivery audit storage.

Demo note:

- Alert-dispatcher also exposes `GET /polling-now` (direct on port `5002`) and `GET /dispatcher/polling-now` (via NGINX on port `5001`) for demo/manual trigger only.
- It executes one immediate poll cycle and is not intended to replace the background poll loop scheduler.

Alert-dispatcher documentation is split into two mandatory files:

- Architecture + justification overview: [ALERT_DISPATCHER_README.md](ALERT_DISPATCHER_README.md)
- Run/setup/test/demo operations guide: [ALERT_DISPATCHER_OPERATIONS.md](ALERT_DISPATCHER_OPERATIONS.md)

#### 1.6. Client (frontend) setup

The browser client is served automatically when you run `docker compose up`
(dev mode: `http://localhost:5003/`, prod mode: `http://localhost:5001/`).
No build step or `npm install` is needed to run it.

For client-specific documentation, including page layouts, browser tests,
diagrams, screenshots, and how to point the client at a remote API, see
[client/client-README.md](client/client-README.md).

#### 1.7. Mock sensor service configuration

Mock sensor source code is in `services/mock_sensor/sender.py`.

You can tune behavior via environment variables:

- `MOCK_SHIPMENT_ID` (default `1`)
- `MOCK_INTERVAL_SECONDS` (default `8`)
- `MOCK_ALERT_EVERY` (default `6`)
- `MOCK_MAX_RETRIES` (default `4`)
- `MOCK_BACKOFF_SECONDS` (default `1`)

Current status in this repository:

- The `mock-sensor` service block is currently commented out in `docker-compose.yml`.
- If you want to demo with automatic fake readings, uncomment the `mock-sensor` service block and run `docker compose up --build` again.

### 2. How to create and populate the database

- **ORM models and functions** are defined in `src/models.py`.
- The repository includes a **database dump** inside **scripts** (`postgres/init/initdb.sh`) to generate and populate the database.
- The `docker-compose.yml` file defines a `postgres-db` container for PostgreSQL (version 15-alpine).

#### 2.1. How to Run

- Run `docker compose up --build`.
  - The `postgres-db` container is created automatically with the database named `coldchain`. The database files are persisted in the `postgres/data` directory.
  - Tables and seed data are automatically created and populated when the `api` service starts.
- How to verify:
  - Run `docker exec -it postgres-db psql -U user -d coldchain` to check if the SQL schema is created.
    - Use the `\dt` command in the `psql` shell to check for tables.

#### 2.2. Other Notes

- No dependencies are needed at this stage except Docker.
- For manual setup, install dependencies, set up PostgreSQL, and run the SQL code in the provided script (`postgres/init/initdb.sh`) to initialize and populate the database. However, this project repo does not officially support manual setup.

### 3. How to use pylint and others below

a. How to set up

```bash
python -m pip install virtualenv
python -m virtualenv .venv

source .venv/bin/activate # OR: .venv\Scripts\activate (for Window CLI)
pip install -r requirements.txt

# Deactivate venv
deactivate
```

b. Prettier / format code
For example

```shell
pylint src
pylint db_init.py # To check

black db_init.py # To fix auto

# ruff check db_init.py
# ruff check db_init.py --fix
```

c. Front-end lint / format (optional)

```bash
cd client
npm install
npm run lint
npm run format:check
npm run format
```

### 4. How to run tests

The project includes a functional testing script that we have implemented using **pytest**.
The tests validate:

- Successful operations (GET, POST, PUT, DELETE)
- Proper HTTP status codes
- Correct JSON responses
- Error handling (400, 403, 404, 415)
- Presence of `Location` header for `201 Created`

Tests use an in-memory SQLite database and do not require Docker.

```bash
sudo mkdir -p instance/cache

pytest -q # Output expected as an example: 43 passed in 0.14s

# If pytest cannot locate the `src` package, run:
PYTHONPATH=. pytest -q

# To see the details of test coverage run:
pytest --cov=src --cov-report=term-missing # Output expected as an example: TOTAL 290 19 98%
```

Alert-dispatcher tests (from repository root):

```bash
pytest -q tests/services/alert_dispatcher

# Run by feature area
pytest -q tests/services/alert_dispatcher/test_webhooks.py
pytest -q tests/services/alert_dispatcher/test_deliveries.py
pytest -q tests/services/alert_dispatcher/test_polling_now.py
pytest -q tests/services/alert_dispatcher/poller

# Optional coverage for auxiliary service
pytest --cov=services.alert_dispatcher --cov-report=term-missing tests/services/alert_dispatcher -q
```

# if import makes trouble:

```bash
PYTHONPATH=. pytest --cov=src --cov-report=term-missing
```

# If you want a more detailed view of what is affecting the coverage:

```bash
pytest --cov=src --cov-report=term-missing -q
```

### 5. How to others

#### 5.1. How to authenticate API requests

- Use the admin API token printed during `docker compose up` (in the `api` container logs) as an API key.
- Add header `Shipmenthub-Api-Key`: <printed_token> to HTTP requests.
- To retrieve the token later, check the container logs: `docker compose logs api | grep "Generated admin"`

#### 5.2. How to check cache

- Access `http://localhost:5001/api/shipments` (GET request) -> Cache files then will be created in `instance/cache/` automatically.

#### 5.2. How to reset DB

```bash
# Stop and remove all containers and volumes
docker compose down -v --remove-orphans  # docker compose -f docker-compose.prod.yml down -v --remove-orphans

# Clean up persistent data
sudo rm -rf postgres/data/
sudo rm -rf instance/cache/
sudo rm services/alert_dispatcher/alert_dispatcher.db

# Restart
docker compose up --build  # docker compose -f docker-compose.prod.yml up --build
```

---

---

---

## Demo Guide

### i. API Routing & Error Handling

```bash
pytest -q tests/test_api.py
```

**What it shows:**

- `404` for unknown routes
- `405` for unsupported HTTP methods

---

### ii. Shipments

```bash
pytest -q tests/test_shipments.py -k "get or post or delete"
```

**What it shows:**

- `GET` → list and retrieve shipments
- `POST` → create shipment (`201 Created`, `Location` header)
- `DELETE` → protected endpoint
- Validation errors (`400`, `415`, `409`)

---

### iii. Authentication & Statelessness

```bash
pytest -q tests/test_shipments.py -k "delete"
```

**What it shows:**

- Delete without API key → `403 Forbidden`
- Delete with API key → `204 No Content`

> Authentication is checked per request using headers. No session is stored. Therefore: API is stateless.

---

### iv. Readings – Child Resources

```bash
pytest -q tests/test_readings.py -k "get or post"
```

**What it shows:**

- Readings belong to shipments
- `POST` creates a reading under a shipment
- `GET` retrieves readings

---

### v. Alerts

```bash
pytest -q tests/test_alerts.py -k "get or put or post"
```

**What it shows:**

- Alerts triggered by temperature violations
- Alerts retrieval
- Alert update (resolve)

---

### vi. Schema Validation

```bash
pytest -q tests/test_shipments.py -k "400 or 415"
```

**What it shows:**

- Missing or invalid fields → `400 Bad Request`
- Non-JSON request body → `415 Unsupported Media Type`
- Required fields are enforced before any data is stored
- Temperature and other fields must match expected data types

---

### vii. Code quality (PyLint)

```bash
pylint src
```

**What it shows:**

- Code structure and style quality
- Score ≥ 9 satisfies requirement #currently ours is 9.82

---

### viii. Test Coverage

```bash
PYTHONPATH=. pytest --cov=src --cov-report=term
```

**What it shows:**

- Coverage of application code (`src`)
- Total coverage ≥ 96% for full points

---

### ix. End-to-end Alert Dispatcher Demo (manual)

This demo shows that creating an out-of-range reading can trigger an alert and then produce a delivery log entry through alert-dispatcher.

1. Start stack (dev or prod):

```bash
docker compose up --build
# or
docker compose -f docker-compose.prod.yml up --build
```

2. Create an out-of-range reading to trigger an alert:

```bash
curl -i -X POST http://localhost:5001/api/shipments/1/readings \
  -H "Content-Type: application/json" \
  -d '{"temp":999,"humidity":40}'
```

3. Trigger one immediate polling cycle (recommended because current compose files set `POLL_INTERVAL_SECONDS=600`):

```bash
# Development route (direct to alert-dispatcher)
curl -i http://localhost:5002/polling-now

# Production route (through nginx)
curl -i http://localhost:5001/dispatcher/polling-now
```

4. Verify delivery logs were updated:

```bash
curl -s http://localhost:5002/deliveries | python3 -m json.tool
```

If you prefer not to call `polling-now`, wait for the configured polling interval and then check deliveries again.

---

### All demo tests in order:

```bash
pytest -q tests/test_api.py
pytest -q tests/test_shipments.py -k "get or post or delete"
pytest -q tests/test_shipments.py -k "delete"
pytest -q tests/test_readings.py -k "get or post"
pytest -q tests/test_alerts.py -k "get or put or post"
```

### All DL4 codes in order

```bash
sudo rm -rf postgres/data/
sudo rm -rf instance/cache/

docker compose down -v --remove-orphans
docker builder prune -f
docker compose up --build
```

## Cloud Deployment (Production)

The full stack is live at http://34.88.97.198:5001/

- Client UI: http://34.88.97.198:5001/
- Main API: http://34.88.97.198:5001/api/shipments
- Alert Dispatcher: http://34.88.97.198:5001/dispatcher/webhooks
- Trigger one polling cycle (demo): http://34.88.97.198:5001/dispatcher/polling-now
- Delivery history: http://34.88.97.198:5001/dispatcher/deliveries

### How to redeploy after pushing backend changes to GitHub

Whenever you push commits that touch the backend (api, alert-dispatcher, models, db_init, dependencies, compose files, nginx config), the VM does not pick them up automatically. SSH in and rebuild.

#### 1. SSH into the VM

```bash
gcloud compute ssh chillsense-vm --zone=europe-north1-a
```

Or use the SSH button next to the VM in the Google Cloud console.

#### 2. Check the current state before changing anything

```bash
cd ~/ChillSense
git status
git branch --show-current
docker-compose -f docker-compose.prod.yml ps
```

`git status` should say working tree clean. If it shows local changes, decide whether to keep or discard them before pulling. `ps` should list five services (postgres-db, api, alert-dispatcher, frontend, nginx), all `Up (healthy)`.

#### 3. See what new commits are coming in

```bash
git fetch
git log HEAD..origin/main --oneline
```

If the second command prints nothing, the VM is already up to date and no redeploy is needed. If it lists commits, those are the changes about to be applied. Press `q` to exit the pager.

#### 4. Stop the running stack

```bash
docker-compose -f docker-compose.prod.yml down --remove-orphans
```

`--remove-orphans` cleans up containers from older compose files that no longer exist. Postgres data is stored on disk at `./postgres/data` (not in a docker-managed volume), so this does NOT delete shipments, readings, or webhook history.

#### 5. Pull the new code

```bash
git pull
```

#### 6. Confirm the host ports are free

Before rebuilding, make sure nothing else grabbed the ports while the stack was down:

```bash
sudo lsof -iTCP -sTCP:LISTEN -P -n | grep -E ':5001|:5432'
```

If this prints anything, another process is using the port and the build will fail when nginx or postgres tries to bind. Kill whatever is holding it before continuing.

#### 7. Build and start the new stack

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

`--build` forces a fresh image build so the new code actually ends up in the containers. `-d` runs detached. First rebuild after big dependency changes can take a few minutes.

#### 8. Verify all services came up healthy

```bash
docker-compose -f docker-compose.prod.yml ps
```

All five services must show `Up (healthy)`. If any shows `unhealthy`, `restarting`, or `Exit`, check its logs:

```bash
docker-compose -f docker-compose.prod.yml logs --tail=50 <service-name>
```

Service names: `api`, `alert-dispatcher`, `frontend`, `nginx`, `postgres-db`.

#### 9. test the endpoints

From inside the VM:

```bash
curl -s -o /dev/null -w "client UI:  %{http_code}\n" http://localhost:5001/
curl -s -o /dev/null -w "api:        %{http_code}\n" http://localhost:5001/api/shipments
curl -s -o /dev/null -w "dispatcher: %{http_code}\n" http://localhost:5001/dispatcher/webhooks
```

All three should return `200`. If any returns something else, check that service's logs.

From your laptop, also open these in a browser to confirm public reachability:

- http://34.88.97.198:5001/
- http://34.88.97.198:5001/api/shipments
- http://34.88.97.198:5001/dispatcher/webhooks

#### 10. (Optional) Trigger one polling cycle

The dispatcher polls every 10 minutes by default. To verify it works without waiting:

```bash
curl http://localhost:5001/dispatcher/polling-now
curl http://localhost:5001/dispatcher/deliveries
```

### Rollback if a redeploy goes wrong

If a new build is broken and you need to get back to the last working state:

```bash
docker-compose -f docker-compose.prod.yml down --remove-orphans
git log --oneline -5                      # find the last good commit hash
git checkout <good-commit-hash>
docker-compose -f docker-compose.prod.yml up --build -d
```

When the fix is ready, switch back with `git checkout main && git pull`.

### How to stop everything

```bash
docker-compose -f docker-compose.prod.yml down
```

### How to stop and wipe everything (full reset including database)

```bash
docker-compose -f docker-compose.prod.yml down -v --remove-orphans
sudo rm -rf postgres/data/
```

### How to check container status

```bash
docker-compose -f docker-compose.prod.yml ps
```

### How to follow live logs

```bash
docker-compose -f docker-compose.prod.yml logs -f api
```

### How to check health of a specific container

```bash
docker inspect <container_name> --format='{{.State.Health.Status}}'
```
