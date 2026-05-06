# Alert Dispatcher Service (Auxiliary)

Alert Dispatcher is a separate auxiliary service for ChillSense.
Its job is to read unresolved alerts from the main API and create delivery logs for webhook notifications.

Main project guide: [README.md](README.md)

## Data model (service-local)

The alert-dispatcher service maintains two local database tables: `Webhook` and `Delivery`. The diagram below shows their structure and how they relate to external entities (`Alert`, `Shipment`) owned by the main ChillSense API.

```mermaid
classDiagram
    class Webhook {
        Integer id
        String name
        String target_url
        Integer status
        DateTime created_at
        DateTime updated_at
    }
    class Delivery {
        Integer id
        Integer alert_id
        Integer shipment_id
        Integer webhook_id
        String target_url
        String status
        Integer response_code
        String error_message
        Integer attempt_count
        DateTime created_at
    }
    class Alert {
        Integer id
        String msg
        String severity
        Boolean is_resolved
        DateTime created_at
    }

    Webhook "1" -- "many" Delivery : has
    Delivery "many" -- "1" Alert : triggered_by
```

## 1. Required justification: why this auxiliary service exists

### 1.1. What this service does (approximation accepted by course requirement)

- It polls unresolved alerts from ChillSense API.
- It processes notification dispatch flow per active webhook.
- It records delivery attempts as operational logs.
- In this project stage, webhook sending is intentionally mocked (`FAKE SEND`).
- This is still valid because the required part is the interaction and service separation.

### 1.2. Why this service is necessary

- Polling and dispatch are ongoing operational tasks, not normal CRUD endpoints.
- Keeping this logic outside the main API helps shipments/readings endpoints stay focused and responsive.
- Dispatcher can be started, restarted, and monitored independently from ChillSense API.
- Webhook configuration and delivery audit logs are cleaner when stored in a dedicated service boundary.

### 1.3. Why implementing directly in ChillSense API is problematic

- Delivery depends on external networks and can be slow, unstable, or temporarily down.
- If delivery logic runs directly in API request paths, user-facing requests can become slower and less reliable.
- Retry/polling behavior can keep API worker processes busy with background concerns.
- Error isolation is weaker: failures in notification flow can affect API runtime behavior.

## 2. Overview in the ecosystem (clear relation to other components)

This is the role of each component:

- ChillSense API (`src/`): source of business data (shipments, readings, alerts).
- Alert Dispatcher (`services/alert_dispatcher/`): background-style worker + API for webhook and delivery logs.
- PostgreSQL: main data for ChillSense API.
- SQLite (`services/alert_dispatcher/alert_dispatcher.db`): local operational data for dispatcher (webhooks and deliveries).
- NGINX (production-like mode): public entry point that routes traffic to both services.

In short:

- ChillSense API is responsible for creating alerts.
- Alert Dispatcher is responsible for consuming unresolved alerts and recording notification delivery attempts.

## 3. How the interaction works (end-to-end)

1. A new reading is posted to ChillSense API.
2. If temperature is out of range, ChillSense API creates an alert.
3. Alert Dispatcher poller calls `GET /api/alerts` on ChillSense API.
4. It filters unresolved alerts (`is_resolved=false`).
5. For each active webhook, it records one delivery attempt via `POST /deliveries`.
6. Delivery history is visible at `GET /deliveries`.

Current implementation note:

- `send_webhook()` is intentionally mocked (`FAKE SEND`) at this stage.
- This is acceptable for the course goal because the required part is the service interaction and separation of responsibilities.

## 4. Service responsibilities

- Manage webhooks (`GET /webhooks`, `PUT /webhooks/<id>`).
- Store delivery records (`GET /deliveries`, `POST /deliveries`).
- Poll unresolved alerts from ChillSense API and create delivery attempts.
- Provide demo/manual trigger endpoint (`GET /polling-now`).

## 5. Architecture diagrams (services, protocols, interaction)

The diagrams below show how services are connected and which communication protocol is used.

### 5.1. Component diagram

```mermaid
flowchart TB
    user["User or Tester"]

    subgraph edge[Edge layer]
        nginx["NGINX reverse proxy - port 5001 - production-like"]
    end

    subgraph app[Application layer]
        direction LR
        dispatcher[Alert Dispatcher service]
        api[ChillSense API service]
        poller[Dispatcher poller loop]
    end

    subgraph data[Data layer]
        pg[(PostgreSQL coldchain)]
        sqlite[(SQLite alert_dispatcher.db)]
    end

    user -->|HTTP port 5001 prod-like| nginx
    nginx -->|HTTP /api/*| api
    nginx -->|HTTP /dispatcher/*| dispatcher

    poller -->|internal call poll_and_dispatch_alerts| dispatcher
    poller -->|HTTP GET /api/alerts| api
    poller -->|HTTP POST /deliveries| dispatcher

    api -->|SQL| pg
    dispatcher -->|SQLite file I/O| sqlite
```

### 5.2. Sequence diagram

```mermaid
sequenceDiagram
    actor Sensor as Sensor/Client
    actor User
    participant N as NGINX
    participant A as ChillSense API service
    participant PG as PostgreSQL
    participant D as Alert Dispatcher API
    participant P as Poller runtime
    participant S as SQLite

    Sensor->>N: POST /api/shipments/{id}/readings
    N->>A: forward request
    A->>PG: INSERT reading
    alt Temperature out of range
        A->>PG: INSERT alert
    end
    A-->>N: 201 response
    N-->>Sensor: 201 response

    Note over P,D: Background poller runs every POLL_INTERVAL_SECONDS

    P->>A: GET /api/alerts
    A->>PG: SELECT alerts
    PG-->>A: result rows
    A-->>P: alerts JSON (includes unresolved)

    loop each unresolved alert x active webhook
        P->>D: POST /deliveries
        D->>S: INSERT delivery
        S-->>D: created or duplicate
        D-->>P: 201 Created or 200 OK
    end

    P-->>D: summary

    opt Demo/manual trigger only
        User->>N: GET /dispatcher/polling-now
        N->>D: forward request
        D->>P: run one poll cycle now
        D-->>N: 200 response
        N-->>User: 200 + summary
    end
```

Deployment notes:

- In production-like mode, public traffic enters through NGINX (NOTE: The diagrams above focus on production-like mode)
- In development mode, alert-dispatcher can also be called directly on port `5002`.

## 6. Operational guide

This operational guide is mandatory documentation for this auxiliary service.

- Run/setup/test/demo instructions: [ALERT_DISPATCHER_OPERATIONS.md](ALERT_DISPATCHER_OPERATIONS.md)

## 7. Documentation format used for public API/functions

Public HTTP endpoints are documented in OpenAPI/Swagger, and internal callable functions are documented with Python docstrings.

Detailed verification steps and endpoint-level checklist are documented in `ALERT_DISPATCHER_OPERATIONS.md` under **Verify API/function documentation requirement**.

