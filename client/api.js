// Shared API helpers for the ChillSense client.
// All three pages (index.html, map.html, shipment.html) import from here.
//
// To point the client at a different backend, change BASE_URL below.
// Local dev:    http://localhost:5001/api
// Cloud VM:     http://34.88.97.198:5001/api
export const BASE_URL = 'http://localhost:5001/api';

// Internal helper. Every public function goes through this so we have one
// place handling response parsing and error throwing.
async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  let resp;
  try {
    resp = await fetch(url, options);
  } catch (e) {
    // network error, CORS block, DNS fail, etc.
    throw new Error(`Network error calling ${path}: ${e.message}`);
  }

  if (!resp.ok) {
    // attach status so callers can show different UI for 404 vs 500 if they want
    const err = new Error(`API ${resp.status} ${resp.statusText} on ${path}`);
    err.status = resp.status;
    throw err;
  }

  // 204 No Content has no body, but we don't hit that path from the client (no DELETE)
  return resp.json();
}

function jsonRequest(path, method, body) {
  return request(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// -------- Shipments --------

export function getShipments() {
  return request('/shipments');
}

export function createShipment(data) {
  return jsonRequest('/shipments', 'POST', data);
}

export function getShipment(id) {
  return request(`/shipments/${id}`);
}

// -------- Readings --------

export function getReadings(shipmentId) {
  return request(`/shipments/${shipmentId}/readings`);
}

// Returns [reading, alert_or_null]. The API automatically creates an alert
// when temp is out of the shipment's min/max range.
export function createReading(shipmentId, data) {
  return jsonRequest(`/shipments/${shipmentId}/readings`, 'POST', data);
}

// -------- Alerts --------

export function getAlerts(shipmentId) {
  return request(`/shipments/${shipmentId}/alerts`);
}

export function resolveAlert(shipmentId, alertId) {
  return jsonRequest(
    `/shipments/${shipmentId}/alerts/${alertId}`,
    'PUT',
    { is_resolved: true },
  );
}
