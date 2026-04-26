FROM python:3.11-slim AS base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
EXPOSE 5000

FROM base AS dev
# CMD ["flask", "--app", "src:create_app", "run", "--host=0.0.0.0", "--port=5000"]

FROM base AS prod
# CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "src:create_app()"]