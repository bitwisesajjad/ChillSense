# PWP SPRING 2026

# PROJECT NAME: ChillSense

## Group information

- Student 1. Sajjad Ghaeminejad (sghaemin25@student.oulu.fi)
- Student 2. Hieu Nguyen (hieu.nguyen@student.oulu.fi)

**Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment**

## How to use

### 1. How to use automatically

```bash
# Development mode (Flask dev server, hot-reload with bind mount)

docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up # http://localhost:5001/

# Production-like mode (NGINX + Gunicorn)
docker compose -f docker-compose.prod.yml up --build # http://localhost:5001/ (served by NGINX, proxied to Gunicorn)
```

#### 1.1. Why two Docker modes?

- Development mode keeps fast iteration and current workflow (live code updates, debug enabled).
- Production mode uses a proper web-server/app-server chain:
  - NGINX handles public HTTP traffic and reverse-proxy routing.
  - Gunicorn runs the Flask WSGI app with worker processes.

#### 1.2. Monitor and control checks (production mode)

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

### 2. How to create and populate the database

- **ORM models and functions** are defined in `src/models.py`.
- The repository includes a **database dump** inside **scripts** (`postgres/init/initdb.sh`) to generate and populate the database.
- The `docker-compose.yml` file defines a `postgres-db` container for PostgreSQL (version 15-alpine).

#### 2.1. How to Run

- Run `docker compose up --build`.
  - The `postgres-db` container is created automatically with the empty database named `coldchain`. The database files in this container are persisted/mounted in the `postgres/data` directory.
- Run `python db_init.py` to create tables and seed data only once
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

- Use the token printed after running `python db_init.py` as an API key.
- Add header `Shipmenthub-Api-Key`: <printed_token> to HTTP requests.

#### 5.2. How to check cache

- Access `http://localhost:5001/api/shipments` (GET request) -> Cache files then will be created in `instance/cache/` automatically.

#### 5.2. How to reset DB

```bash
(sudo rm -rf postgres/data/)
python db_init.py
sudo rm -rf instance/cache/
```

---

---

---

## Demo Guide (For Presentation)

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

### All demo tests in order:

```bash
pytest -q tests/test_api.py
pytest -q tests/test_shipments.py -k "get or post or delete"
pytest -q tests/test_shipments.py -k "delete"
pytest -q tests/test_readings.py -k "get or post"
pytest -q tests/test_alerts.py -k "get or put or post"
```
