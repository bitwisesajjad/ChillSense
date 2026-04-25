FROM python:3.11-slim

WORKDIR /app

COPY services/alert_dispatcher/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/alert_dispatcher /app/services/alert_dispatcher

EXPOSE 5002
