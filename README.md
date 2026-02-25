# PWP SPRING 2026
# PROJECT NAME: ChillSense
## Group information
* Student 1. Sajjad Ghaeminejad (sghaemin25@student.oulu.fi)
* Student 2. Hieu Nguyen (hieu.nguyen@student.oulu.fi)
* Student 3. Name and email
* Student 4. Name and email


__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment__

## How to use
### How to use automatically
```bash
docker compose up --build # docker-compose up --build
# or
docker compose up # docker-compose up
```

### How to use manually
1. How to set up
```bash
python -m pip install virtualenv
python -m virtualenv .venv

source .venv/bin/activate # OR: .venv\Scripts\activate (for Window CLI)
pip install -r requirements.txt

# Deactivate venv
deactivate
```

2. How to run
```bash
python app.py # OR: flask run
```

3. Prettier / format code
For example
```shell
pylint db_init.py # To check

black db_init.py # To fix auto

# ruff check db_init.py
# ruff check db_init.py --fix
```

## Explain
### How to create and populate the database
- **ORM models and functions** are defined in `src/models.py`.
- The repository includes a **database dump** inside **scripts** (`postgres/init/initdb.sh`) to generate and populate the database.
- The `docker-compose.yml` file defines a `postgres-db` container for PostgreSQL (version 15-alpine).

#### 1. How to Run
- Run `docker compose up --build`.
  - The `postgres-db` container is created automatically with the empty database named `coldchain`. The database files in this container are persisted/mounted in the `postgres/data` directory.
- Run `python db_init.py` to create tables and seed data only once
- How to verify:
  - Run `docker exec -it postgres-db psql -U user -d coldchain` to check if the SQL schema is created.
    - Use the `\dt` command in the `psql` shell to check for tables.
#### 2. Other Notes
- No dependencies are needed at this stage except Docker.
- For manual setup, install dependencies, set up PostgreSQL, and run the SQL code in the provided script (`postgres/init/initdb.sh`) to initialize and populate the database. However, this project repo does not officially support manual setup.
