FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app/services/alert_dispatcher

EXPOSE 5002
