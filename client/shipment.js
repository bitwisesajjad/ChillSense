// Detail page logic. Loads one shipment and its readings + alerts, renders
// the info card, the temperature chart (Chart.js), the readings table, the
// alerts table with a resolve button, and the sensor simulator.
//
// Pure helpers and render functions are exported so tests/test_shipment.html
// can exercise them without a real API or a real Chart.js instance.

import { getShipment, getReadings, getAlerts, createReading, resolveAlert } from './api.js';

const ALERT_COLOR = '#ee0000';
const NORMAL_COLOR = '#009966';

//  pure helpers 

export function getShipmentIdFromUrl(search) {
  const params = new URLSearchParams(search || '');
  const raw = params.get('id');
  if (raw === null) return null;
  const n = parseInt(raw, 10);
  if (Number.isNaN(n)) return null;
  return n;
}

// Walk readings in chronological order and produce arrays Chart.js can plot.
// pointColors flags which points violated the shipment thresholds.
export function buildChartData(readings, shipment) {
  // copy and sort ascending so the line goes left-to-right in time
  const sorted = [...readings].sort((a, b) =>
    (a.ts || '').localeCompare(b.ts || '')
  );

  const labels = sorted.map(r => r.ts);
  const temps = sorted.map(r => r.temp);
  const pointColors = sorted.map(r => {
    const out = r.temp < shipment.min_temperature || r.temp > shipment.max_temperature;
    return out ? ALERT_COLOR : NORMAL_COLOR;
  });

  return {
    labels,
    temps,
    pointColors,
    minLine: shipment.min_temperature,
    maxLine: shipment.max_temperature,
  };
}

// Pick a random temp inside the shipment's safe range, biased toward the middle.
export function pickSafeTemp(shipment) {
  const min = shipment.min_temperature;
  const max = shipment.max_temperature;
  // small inset so we don't accidentally land on the boundary
  const pad = (max - min) * 0.1;
  const lo = min + pad;
  const hi = max - pad;
  if (lo >= hi) return (min + max) / 2;
  return Math.round((lo + Math.random() * (hi - lo)) * 10) / 10;
}

// Pick a temp outside the safe range, alternating between too-cold and too-hot.
export function pickViolationTemp(shipment) {
  const goHigh = Math.random() < 0.5;
  const offset = 1 + Math.random() * 4; // 1 to 5 degrees past the threshold
  if (goHigh) {
    return Math.round((shipment.max_temperature + offset) * 10) / 10;
  }
  return Math.round((shipment.min_temperature - offset) * 10) / 10;
}

// API timestamps come in as "YYYY-MM-DD HH:MM:SS". Trim the seconds and
// return something a bit shorter for the table.
export function formatTimestamp(ts) {
  if (!ts) return '-';
  // string is already short enough; trim seconds if present
  const m = String(ts).match(/^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})/);
  if (m) return `${m[1]} ${m[2]}`;
  return String(ts);
}

//  DOM rendering 

export function renderShipmentInfo(container, shipment) {
  container.querySelector('#info-name').textContent = shipment.name;
  container.querySelector('#info-route').textContent =
    `${shipment.origin} → ${shipment.destination}`;
  container.querySelector('#info-status').textContent = shipment.status || 'unknown';
  container.querySelector('#info-temp-range').textContent =
    `${shipment.min_temperature} / ${shipment.max_temperature} °C`;
  container.querySelector('#info-created').textContent =
    formatTimestamp(shipment.created_at);
}

export function renderReadingsTable(tbody, readings) {
  tbody.innerHTML = '';

  if (!readings || readings.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 4;
    td.className = 'empty';
    td.textContent = 'No readings yet';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  // newest first
  const sorted = [...readings].sort((a, b) =>
    (b.ts || '').localeCompare(a.ts || '')
  );

  for (const r of sorted) {
    const tr = document.createElement('tr');

    const idTd = document.createElement('td');
    idTd.className = 'mono';
    idTd.textContent = r.id;

    const tempTd = document.createElement('td');
    tempTd.className = 'mono';
    tempTd.textContent = `${r.temp} °C`;

    const humTd = document.createElement('td');
    humTd.className = 'mono';
    humTd.textContent = r.humidity == null ? '-' : `${r.humidity} %`;

    const tsTd = document.createElement('td');
    tsTd.className = 'mono dim';
    tsTd.textContent = r.ts;

    tr.append(idTd, tempTd, humTd, tsTd);
    tbody.appendChild(tr);
  }
}

export function renderAlertsTable(tbody, alerts, onResolve) {
  tbody.innerHTML = '';

  if (!alerts || alerts.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 6;
    td.className = 'empty';
    td.textContent = 'No alerts';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  // newest first
  const sorted = [...alerts].sort((a, b) =>
    (b.created_at || '').localeCompare(a.created_at || '')
  );

  for (const a of sorted) {
    const tr = document.createElement('tr');

    const idTd = document.createElement('td');
    idTd.className = 'mono';
    idTd.textContent = a.id;

    const msgTd = document.createElement('td');
    msgTd.textContent = a.msg;

    const sevTd = document.createElement('td');
    const sevBadge = document.createElement('span');
    sevBadge.className = `badge sev-${a.severity || 'warning'}`;
    sevBadge.textContent = a.severity || 'warning';
    sevTd.appendChild(sevBadge);

    const resTd = document.createElement('td');
    resTd.className = 'mono';
    resTd.textContent = a.is_resolved ? 'yes' : 'no';

    const tsTd = document.createElement('td');
    tsTd.className = 'mono dim';
    tsTd.textContent = a.created_at;

    const actTd = document.createElement('td');
    if (!a.is_resolved) {
      const btn = document.createElement('button');
      btn.className = 'btn btn-secondary resolve-btn';
      btn.type = 'button';
      btn.textContent = 'Resolve';
      btn.addEventListener('click', () => onResolve(a.id));
      actTd.appendChild(btn);
    }

    tr.append(idTd, msgTd, sevTd, resTd, tsTd, actTd);
    tbody.appendChild(tr);
  }
}

//  chart wiring (only runs in the browser) 

let chartInstance = null;

function renderChart(canvas, chartData) {
  // Chart.js is loaded globally via the script tag in shipment.html
  if (typeof window === 'undefined' || typeof window.Chart === 'undefined') return;

  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const ctx = canvas.getContext('2d');
  // we use a single line dataset and color individual points,
  // plus two flat datasets for the min/max threshold lines
  const minThresh = new Array(chartData.labels.length).fill(chartData.minLine);
  const maxThresh = new Array(chartData.labels.length).fill(chartData.maxLine);

  chartInstance = new window.Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Temperature',
          data: chartData.temps,
          borderColor: '#666',
          backgroundColor: 'transparent',
          pointBackgroundColor: chartData.pointColors,
          pointBorderColor: chartData.pointColors,
          pointRadius: 4,
          tension: 0.2,
        },
        {
          label: 'Min threshold',
          data: minThresh,
          borderColor: '#3b82f6',
          borderDash: [6, 4],
          pointRadius: 0,
          fill: false,
        },
        {
          label: 'Max threshold',
          data: maxThresh,
          borderColor: ALERT_COLOR,
          borderDash: [6, 4],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { title: { display: true, text: '°C' } },
        x: { ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 8 } },
      },
      plugins: {
        legend: { position: 'bottom' },
      },
    },
  });
}

//  page bootstrap 

let currentShipment = null;

async function loadDetail(shipmentId) {
  const errorEl = document.getElementById('error-banner');
  errorEl.style.display = 'none';

  let shipment, readings, alerts;
  try {
    [shipment, readings, alerts] = await Promise.all([
      getShipment(shipmentId),
      getReadings(shipmentId),
      getAlerts(shipmentId),
    ]);
  } catch (e) {
    errorEl.textContent = `Failed to load shipment ${shipmentId}: ${e.message}`;
    errorEl.style.display = 'block';
    return;
  }

  currentShipment = shipment;

  document.getElementById('breadcrumb-id').textContent = `#${shipment.id}`;
  renderShipmentInfo(document.getElementById('info-card'), shipment);
  renderReadingsTable(document.getElementById('readings-tbody'), readings);

  const onResolve = async (alertId) => {
    try {
      await resolveAlert(shipment.id, alertId);
      // re-fetch and re-render alerts
      const fresh = await getAlerts(shipment.id);
      renderAlertsTable(document.getElementById('alerts-tbody'), fresh, onResolve);
    } catch (err) {
      const simMsg = document.getElementById('sim-msg');
      simMsg.textContent = `Failed to resolve alert: ${err.message}`;
      simMsg.className = 'form-msg err';
    }
  };
  renderAlertsTable(document.getElementById('alerts-tbody'), alerts, onResolve);

  const canvas = document.getElementById('temp-chart');
  if (canvas) {
    const chartData = buildChartData(readings, shipment);
    renderChart(canvas, chartData);
  }
}

function wireSimulator() {
  const sendSafe = document.getElementById('sim-safe');
  const sendViolation = document.getElementById('sim-violation');
  const sendCustom = document.getElementById('sim-custom');
  const tempInput = document.getElementById('sim-temp');
  const humInput = document.getElementById('sim-humidity');
  const simMsg = document.getElementById('sim-msg');

  async function send(temp, humidity) {
    if (!currentShipment) return;
    simMsg.textContent = '';
    simMsg.className = 'form-msg';

    const payload = { temp };
    if (humidity != null && !Number.isNaN(humidity)) payload.humidity = humidity;

    try {
      const result = await createReading(currentShipment.id, payload);
      const alertObj = result[1];
      if (alertObj) {
        simMsg.textContent = 'Reading added — alert triggered';
        simMsg.classList.add('err');
      } else {
        simMsg.textContent = 'Reading added — no alert';
        simMsg.classList.add('ok');
      }
      // refresh tables and chart
      await loadDetail(currentShipment.id);
    } catch (err) {
      simMsg.textContent = `Failed to send reading: ${err.message}`;
      simMsg.classList.add('err');
    }
  }

  sendSafe.addEventListener('click', () => {
    const t = pickSafeTemp(currentShipment);
    send(t, parseFloat(humInput.value) || null);
  });
  sendViolation.addEventListener('click', () => {
    const t = pickViolationTemp(currentShipment);
    send(t, parseFloat(humInput.value) || null);
  });
  sendCustom.addEventListener('click', () => {
    const t = parseFloat(tempInput.value);
    if (Number.isNaN(t)) {
      simMsg.textContent = 'Enter a temperature first';
      simMsg.className = 'form-msg err';
      return;
    }
    send(t, parseFloat(humInput.value) || null);
  });
}

// only run page logic when we're on shipment.html
if (typeof document !== 'undefined' && document.getElementById('readings-tbody')) {
  const id = getShipmentIdFromUrl(window.location.search);
  if (id == null) {
    const err = document.getElementById('error-banner');
    err.textContent = 'Missing shipment id in URL';
    err.style.display = 'block';
  } else {
    wireSimulator();
    loadDetail(id);
  }
}
