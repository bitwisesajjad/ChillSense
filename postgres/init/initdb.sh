# #!/usr/bin/env bash
# set -e

# echo "Success start"

# # Create tables + seed data
# psql -v ON_ERROR_STOP=1 -U user -d coldchain <<'EOSQL'
#   -- Shipments table
#   CREATE TABLE IF NOT EXISTS public.shipments (
#     id SERIAL PRIMARY KEY,
#     name varchar(100) NOT NULL,
#     origin varchar(50) NOT NULL,
#     destination varchar(50) NOT NULL,
#     status varchar(20) DEFAULT 'active',
#     min_temperature double precision DEFAULT -25.0,
#     max_temperature double precision DEFAULT -18.0,
#     created_at timestamp NOT NULL DEFAULT NOW()
#   );

#   -- Readings table
#   CREATE TABLE IF NOT EXISTS public.readings (
#     id SERIAL PRIMARY KEY,
#     temp double precision NOT NULL,
#     humidity double precision,
#     shipment_id integer REFERENCES public.shipments(id) ON DELETE SET NULL,
#     ts timestamp NOT NULL DEFAULT NOW()
#   );

#   -- Alerts table
#   CREATE TABLE IF NOT EXISTS public.alerts (
#     id SERIAL PRIMARY KEY,
#     msg varchar(200),
#     severity varchar(20) DEFAULT 'warning',
#     is_resolved boolean DEFAULT FALSE,
#     shipment_id integer REFERENCES public.shipments(id) ON DELETE SET NULL,
#     reading_id integer UNIQUE REFERENCES public.readings(id) ON DELETE SET NULL,
#     created_at timestamp NOT NULL DEFAULT NOW()
#   );

#   -- Audit logs table
#   CREATE TABLE IF NOT EXISTS public.audit_logs (
#     id SERIAL PRIMARY KEY,
#     action varchar(50),
#     details varchar(200),
#     ts timestamp NOT NULL DEFAULT NOW()
#   );

#   -- Seed shipments
#   INSERT INTO public.shipments (id, name, origin, destination, status, min_temperature, max_temperature) VALUES
#     (1, 'Truck-001 (Pfizer)', 'Berlin', 'Munich', 'active', 2.0, 8.0),
#     (2, 'Truck-101 (Maersk-Meat)', 'Oslo', 'Hamburg', 'active', -25.0, -18.0),
#     (3, 'Truck-201 (Chiquita)', 'Quito', 'Rotterdam', 'active', 12.0, 14.0)
#   ON CONFLICT (id) DO NOTHING;

#   -- Seed readings
#   INSERT INTO public.readings (id, temp, humidity, shipment_id) VALUES
#     (1, 5.5, 65.0, 1),
#     (2, -20.5, 80.0, 2),
#     (3, 13.0, 90.0, 3)
#   ON CONFLICT (id) DO NOTHING;

#   -- Seed alerts (có reading_id)
#   INSERT INTO public.alerts (id, msg, severity, is_resolved, shipment_id, reading_id) VALUES
#     (1, 'Temperature above threshold for vaccine cargo', 'critical', FALSE, 1, 1),
#     (2, 'Temperature below threshold for meat cargo', 'warning', TRUE, 2, 2)
#   ON CONFLICT (id) DO NOTHING;

#   -- Seed audit logs
#   INSERT INTO public.audit_logs (id, action, details) VALUES
#     (1, 'CREATE_SHIPMENT', 'Seed shipment Truck-001 (Pfizer)'),
#     (2, 'CREATE_READING', 'Initial reading for Truck-001 (Pfizer)')
#   ON CONFLICT (id) DO NOTHING;

#   -- DEBUG: Update sequences to prevent conflicts with future inserts
#   SELECT setval('shipments_id_seq', (SELECT MAX(id) FROM shipments));
#   SELECT setval('readings_id_seq', (SELECT MAX(id) FROM readings));
#   SELECT setval('alerts_id_seq', (SELECT MAX(id) FROM alerts));
#   SELECT setval('audit_logs_id_seq', (SELECT MAX(id) FROM audit_logs));
# EOSQL

# echo "Success end"

# # CONSTRAINT fk_shipment FOREIGN KEY (shipment_id) REFERENCES public.shipments(id) ON DELETE SET NULL,

# # docker exec -it postgres-db psql -U user -d coldchain
# # \dt
# # SELECT * FROM shipments;
# # SELECT * FROM readings;