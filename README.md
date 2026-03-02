# PWP SPRING 2026

# PROJECT NAME: ChillSense

## Group information

- Student 1. Sajjad Ghaeminejad (sghaemin25@student.oulu.fi)
- Student 2. Hieu Nguyen (hieu.nguyen@student.oulu.fi)

**Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment**

## How to use

### 1. How to use automatically

```bash
docker compose up --build # docker-compose up --build # http://localhost:5001/
docker compose up # docker-compose up
```

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
pytest -q # Output expected as an example: 15 passed in 0.14s

# If pytest cannot locate the `src` package, run:
PYTHONPATH=. pytest -q

# To see the details of test coverage run:
pytest --cov=src --cov-report=term-missing # Output expected as an example: TOTAL 290 19 93%
```

### 5. How to others
- Cache example `http://localhost:5001/api/shipments`
  - Then `http://localhost:5001/api/shipments?page=0` should work
  - Also some cache files should appear in `instance/cache/`
