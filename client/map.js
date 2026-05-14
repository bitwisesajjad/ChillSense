// Map page logic. Pulls all shipments + their alerts and draws a polyline
// per shipment between origin and destination on a Leaflet map. Routes are
// colored red when the shipment has any unresolved alerts, green otherwise.
//
// The pure helpers are exported so tests/test_map.html can exercise them
// without loading Leaflet.

import { getShipments, getReadings, getAlerts } from './api.js';

const ALERT_COLOR = '#ee0000';
const SAFE_COLOR = '#009966';

// City lookup. Handover originally listed only Finnish cities, but the
// seed data uses European cities (Berlin, Oslo, etc.) so we include those
// too. Coords are roughly the city center.
export const CITY_COORDS = {
  // Finland
  Oulu: [65.0121, 25.4651],
  Helsinki: [60.1699, 24.9384],
  Tampere: [61.4978, 23.761],
  Turku: [60.4518, 22.2666],
  Jyväskylä: [62.2426, 25.7473],
  Rovaniemi: [66.5039, 25.7294],
  Kuopio: [62.898, 27.6782],
  Lahti: [60.9827, 25.6612],
  // Europe (matches db_init.py seed)
  Berlin: [52.52, 13.405],
  Munich: [48.1351, 11.582],
  Oslo: [59.9139, 10.7522],
  Hamburg: [53.5511, 9.9937],
  Rotterdam: [51.9244, 4.4777],
  Amsterdam: [52.3676, 4.9041],
  // European capitals
  Stockholm: [59.3293, 18.0686],
  Copenhagen: [55.6761, 12.5683],
  Paris: [48.8566, 2.3522],
  Madrid: [40.4168, -3.7038],
  Lisbon: [38.7223, -9.1393],
  Rome: [41.9028, 12.4964],
  Vienna: [48.2082, 16.3738],
  Warsaw: [52.2297, 21.0122],
  Prague: [50.0755, 14.4378],
  Brussels: [50.8503, 4.3517],
  // South America (Chiquita route)
  Quito: [-0.1807, -78.4678],
};

//  pure helpers

export function getCoords(city) {
  if (!city) return null;
  return CITY_COORDS[city] ?? null;
}

export function routeColor(hasUnresolved) {
  return hasUnresolved ? ALERT_COLOR : SAFE_COLOR;
}

export function unresolvedCount(alerts) {
  if (!alerts) return 0;
  return alerts.filter(a => !a.is_resolved).length;
}

// Bearing from point a to point b, in degrees clockwise from north.
// Used to rotate the arrowhead so it points along the route.
export function bearingDegrees(a, b) {
  const toRad = d => (d * Math.PI) / 180;
  const toDeg = r => (r * 180) / Math.PI;

  const lat1 = toRad(a[0]);
  const lat2 = toRad(b[0]);
  const dLng = toRad(b[1] - a[1]);

  const y = Math.sin(dLng) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);

  return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

export function latestReadingTemp(readings) {
  if (!readings || readings.length === 0) return null;
  // string sort by ts works because the API uses "YYYY-MM-DD HH:MM:SS"
  const sorted = [...readings].sort((a, b) =>
    (b.ts || '').localeCompare(a.ts || '')
  );
  return sorted[0].temp;
}

export function buildPopupHtml(shipment, latestTemp, alertCount) {
  const tempText = latestTemp == null ? '-' : `${latestTemp} °C`;
  const safeName = String(shipment.name).replace(/[<>&]/g, '');
  return `
    <div style="font-family: 'Geist', system-ui, sans-serif; font-size: 13px; min-width: 180px;">
      <div style="font-weight: 600; margin-bottom: 4px;">${safeName}</div>
      <div style="color: #666; margin-bottom: 8px;">
        ${shipment.origin} → ${shipment.destination}
      </div>
      <div style="display: grid; grid-template-columns: auto 1fr; gap: 4px 12px;">
        <div style="color: #666;">Status</div>
        <div>${shipment.status || '-'}</div>
        <div style="color: #666;">Latest temp</div>
        <div style="font-family: 'Geist Mono', monospace;">${tempText}</div>
        <div style="color: #666;">Alerts</div>
        <div style="font-family: 'Geist Mono', monospace;">${alertCount}</div>
      </div>
      <div style="margin-top: 10px;">
        <a href="shipment.html?id=${shipment.id}"
           style="color: #009966; font-weight: 500; text-decoration: none;">
          View detail →
        </a>
      </div>
    </div>
  `;
}

// Build everything the map needs for one shipment, or null if a city is unknown.
export function buildRoute(shipment, alerts, readings) {
  const a = getCoords(shipment.origin);
  const b = getCoords(shipment.destination);
  if (!a || !b) return null;

  const count = unresolvedCount(alerts);
  const color = routeColor(count > 0);
  const latestTemp = latestReadingTemp(readings);
  const popupHtml = buildPopupHtml(shipment, latestTemp, alerts.length);

  return {
    coords: [a, b],
    color,
    popupHtml,
    shipmentId: shipment.id,
    bearing: bearingDegrees(a, b),
  };
}

//  Leaflet bootstrap (only runs in the browser)

async function loadMap() {
  const errorEl = document.getElementById('error-banner');
  errorEl.style.display = 'none';

  let shipments;
  try {
    shipments = await getShipments();
  } catch (e) {
    errorEl.textContent = `Failed to load shipments: ${e.message}`;
    errorEl.style.display = 'block';
    return;
  }

  // initialize the Leaflet map centered roughly on Europe so the seed data is visible
  const map = window.L.map('leaflet-map', {
    center: [55.0, 15.0],
    zoom: 4,
  });

  window.L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> ' +
        '&copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 19,
    }
  ).addTo(map);

  // pull alerts + readings for each shipment in parallel
  const drawables = await Promise.all(
    shipments.map(async s => {
      let alerts = [],
        readings = [];
      try {
        alerts = await getAlerts(s.id);
      } catch {
        /* skip */
      }
      try {
        readings = await getReadings(s.id);
      } catch {
        /* skip */
      }
      return { shipment: s, alerts, readings };
    })
  );

  const skipped = [];
  const allLatLngs = [];

  for (const d of drawables) {
    const route = buildRoute(d.shipment, d.alerts, d.readings);
    if (!route) {
      skipped.push(`${d.shipment.origin} → ${d.shipment.destination}`);
      console.warn(
        `Skipping shipment ${d.shipment.id} (${d.shipment.name}): ` +
          `unknown city in route ${d.shipment.origin} → ${d.shipment.destination}`
      );
      continue;
    }

    const line = window.L.polyline(route.coords, {
      color: route.color,
      weight: 3,
      opacity: 0.85,
    }).addTo(map);
    line.bindPopup(route.popupHtml);

    // origin gets a circle marker, destination gets an arrowhead so the
    // direction of travel is obvious at a glance
    const [origin, destination] = route.coords;

    window.L.circleMarker(origin, {
      radius: 6,
      color: route.color,
      fillColor: route.color,
      fillOpacity: 1,
      weight: 2,
    })
      .addTo(map)
      .bindPopup(route.popupHtml);

    // SVG triangle inside a divIcon, rotated to follow the route bearing.
    // The triangle's tip points up by default, so we rotate by (bearing - 0)
    // since Leaflet's bearing convention matches "0 = north = up on screen".
    const arrowSvg = `
      <svg viewBox="0 0 20 20" width="20" height="20"
           style="transform: rotate(${route.bearing}deg); transform-origin: 50% 50%;">
        <polygon points="10,1 18,18 10,14 2,18"
                 fill="${route.color}" stroke="${route.color}" stroke-width="1"
                 stroke-linejoin="round"/>
      </svg>
    `;
    const arrowIcon = window.L.divIcon({
      className: 'route-arrow',
      html: arrowSvg,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });
    window.L.marker(destination, { icon: arrowIcon })
      .addTo(map)
      .bindPopup(route.popupHtml);

    allLatLngs.push(origin, destination);
  }

  // fit bounds so the user sees all routes at once
  if (allLatLngs.length > 0) {
    map.fitBounds(allLatLngs, { padding: [40, 40] });
  }

  // update the skipped notice if any
  const skippedEl = document.getElementById('skipped-notice');
  if (skippedEl && skipped.length > 0) {
    skippedEl.textContent = `${skipped.length} route(s) skipped (unknown city): ${skipped.join(', ')}`;
    skippedEl.style.display = 'block';
  }
}

// only run page logic when we're on map.html
if (typeof document !== 'undefined' && document.getElementById('leaflet-map')) {
  loadMap();
}
