"""Periodic mock sensor sender for ChillSense readings endpoint."""

import datetime as dt
import os
import random
import time
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class APIDataSource:
    """Requests Session wrapper with retry and self-healing session reset."""

    def __init__(
        self,
        host,
        api_key=None,
        timeout_seconds=5,
        max_retries=3,
        backoff_seconds=1.0,
    ):
        host = host or "http://localhost:5000"
        assert host.startswith("http"), "No protocol in host address"
        self.host = host
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = self._build_session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.session.close()

    def _build_session(self):
        session = requests.Session()
        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        if self.api_key:
            session.headers.update({"Shipmenthub-Api-Key": self.api_key})

        retry_policy = Retry(
            total=self.max_retries,
            connect=self.max_retries,
            read=self.max_retries,
            status=self.max_retries,
            backoff_factor=self.backoff_seconds,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _reset_session(self):
        self.session.close()
        self.session = self._build_session()

    def _request(self, method, uri, expected_statuses, data=None):
        attempts = self.max_retries + 1
        endpoint = urljoin(self.host, uri)

        for attempt in range(1, attempts + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                print(f"Request error on attempt {attempt}/{attempts}: {exc}")
                if attempt == attempts:
                    raise
                self._reset_session()
                time.sleep(self.backoff_seconds * attempt)
                continue

            if response.status_code in expected_statuses:
                return response

            should_retry = response.status_code in (401, 403, 408, 425, 429, 500, 502, 503, 504)
            if should_retry and attempt < attempts:
                print(
                    f"HTTP {response.status_code} on attempt {attempt}/{attempts}, "
                    "resetting session and retrying"
                )
                self._reset_session()
                time.sleep(self.backoff_seconds * attempt)
                continue

            raise RuntimeError(
                f"Request failed for {method} {uri}: "
                f"status={response.status_code}, body={response.text}"
            )

        raise RuntimeError(f"Exceeded retry attempts for {method} {uri}")

    def healthcheck(self):
        response = self._request("GET", "/health", (200,))
        return response.json()

    def get_shipment(self, shipment_id):
        response = self._request("GET", f"/api/shipments/{shipment_id}", (200,))
        return response.json()

    def create_reading(self, shipment_id, payload):
        response = self._request(
            "POST",
            f"/api/shipments/{shipment_id}/readings",
            (201,),
            data=payload,
        )
        return response.json()


def read_api_key(path="/run/secrets/chillsense_api_key"):
    """Read API key when mounted as docker secret/file. Optional for reading posts."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as source:
        value = source.read().strip()
    return value or None


def generate_temp(min_temperature, max_temperature, seq, alert_every):
    """Generate mostly-normal temperatures with periodic threshold violations."""
    if alert_every > 0 and seq % alert_every == 0:
        if (seq // alert_every) % 2 == 0:
            return round(max_temperature + random.uniform(0.7, 3.0), 2)
        return round(min_temperature - random.uniform(0.7, 3.0), 2)

    safe_min = min_temperature + 0.3
    safe_max = max_temperature - 0.3
    if safe_min >= safe_max:
        center = (min_temperature + max_temperature) / 2.0
        return round(center, 2)
    return round(random.uniform(safe_min, safe_max), 2)


def main():
    api_host = os.getenv("MOCK_API_HOST", "http://api:5000")
    shipment_id = int(os.getenv("MOCK_SHIPMENT_ID", "1"))
    interval_seconds = float(os.getenv("MOCK_INTERVAL_SECONDS", "8"))
    humidity_min = float(os.getenv("MOCK_HUMIDITY_MIN", "45"))
    humidity_max = float(os.getenv("MOCK_HUMIDITY_MAX", "80"))
    alert_every = int(os.getenv("MOCK_ALERT_EVERY", "6"))
    timeout_seconds = float(os.getenv("MOCK_TIMEOUT_SECONDS", "5"))
    max_retries = int(os.getenv("MOCK_MAX_RETRIES", "4"))
    backoff_seconds = float(os.getenv("MOCK_BACKOFF_SECONDS", "1.0"))
    startup_wait_seconds = float(os.getenv("MOCK_STARTUP_WAIT_SECONDS", "3"))

    api_key = os.getenv("SHIPMENTHUB_API_KEY") or read_api_key()

    with APIDataSource(
        api_host,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    ) as api:
        while True:
            try:
                api.healthcheck()
                break
            except Exception as exc:  # pylint: disable=broad-except
                print(f"API not ready yet: {exc}")
                time.sleep(startup_wait_seconds)

        while True:
            try:
                shipment = api.get_shipment(shipment_id)
                min_temperature = float(shipment["min_temperature"])
                max_temperature = float(shipment["max_temperature"])
                break
            except Exception as exc:  # pylint: disable=broad-except
                print(f"Shipment {shipment_id} not ready yet: {exc}")
                time.sleep(startup_wait_seconds)

        print(
            "Mock sensor started for shipment "
            f"{shipment_id} with range [{min_temperature}, {max_temperature}]"
        )

        seq = 1
        while True:
            temp = generate_temp(min_temperature, max_temperature, seq, alert_every)
            humidity = round(random.uniform(humidity_min, humidity_max), 2)
            payload = {
                "temp": temp,
                "humidity": humidity,
            }

            try:
                created = api.create_reading(shipment_id, payload)
                reading = created[0]
                maybe_alert = created[1]
                status = "ALERT" if maybe_alert else "OK"
                print(
                    f"[{dt.datetime.utcnow().isoformat()}Z] "
                    f"reading_id={reading['id']} temp={temp} humidity={humidity} {status}"
                )
            except Exception as exc:  # pylint: disable=broad-except
                print(f"Failed to create reading for shipment {shipment_id}: {exc}")

            seq += 1
            time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
