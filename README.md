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
```
black .
```

## Explain
### How to create and populate the database
1. The `docker-compose.yml` file defines a `postgres-db` container for the PostgreSQL database.
2. When you run `docker compose up --build`, the `postgres-db` container automatically executes the script `postgres/init/initdb.sh` (this file follows `src/models.py` file) to create the database structure and seed initial data.
3. The database files are persisted in the `postgres/data` directory.