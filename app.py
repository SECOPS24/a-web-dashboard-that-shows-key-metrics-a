from flask import Flask, jsonify, render_template_string, request
from datetime import datetime, timedelta
import random
import math

app = Flask(__name__)

# --- Data Generation ---

CATEGORIES = ["Electronics", "Clothing", "Food & Beverage", "Sports", "Home & Garden"]

def generate_data(start_date, end_date, categories):
    data = []
    current = start_date
    while current <= end_date:
        for cat in categories:
            base = {"Electronics": 1200, "Clothing": 800, "Food & Beverage": 600, "Sports": 500, "Home & Garden": 400}[cat]
            noise = random.uniform(0.7, 1.4)
            seasonal = 1 + 0.3 * math.sin(2 * math.pi * current.timetuple().tm_yday / 365)
            revenue = round(base * noise * seasonal, 2)
            units = random.randint(20, 200)
            profit_margin = random.uniform(0.15, 0.45)
            data.append({
                "date": current.strftime("%Y-%m-%d"),
                "category": cat,
                "revenue": revenue,
                "units": units,
                "profit": round(revenue * profit_margin, 2),
                "customers": random.randint(10, 150),
                "returns": random.randint(0, int(units * 0.1))
            })
        current += timedelta(days=1)
    return data


random.seed(42)
ALL_DATA = generate_data(
    datetime(2024, 1, 1),
    datetime(2024, 12, 31),
    CATEGORIES
)


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/metrics")
def api_metrics():
    start_str = request.args.get("start", "2024-01-01")
    end_str = request.args.get("end", "2024-03-31")
    cats = request.args.getlist("categories")
    if not cats:
        cats = CATEGORIES[:]

    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    filtered = [
        d for d in ALL_DATA
        if start_dt <= datetime.strptime(d["date"], "%Y-%m-%d") <= end_dt
        and d["category"] in cats
    ]

    # --- KPI Cards ---
    total_revenue = sum(d["revenue"] for d in filtered)
    total_profit = sum(d["profit"] for d in filtered)
    total_units = sum(d["units"] for d in filtered)
    total_customers = sum(d["customers"] for d in filtered)
    total_returns = sum(d["returns"] for d in filtered)
    avg_margin = (total_profit / total_revenue * 100) if total_revenue else 0

    # --- Revenue Over Time (daily aggregated) ---
    daily = {}
    for d in filtered:
        dt = d["date"]
        if dt not in daily:
            daily[dt] = {"revenue": 0, "profit": 0, "units": 0}
        daily[dt]["revenue"] += d["revenue"]
        daily[dt]["profit"] += d["profit"]
        daily[dt]["units"] += d["units"]
    daily_sorted = sorted(daily.items())
    timeline_labels = [x[0] for x in daily_sorted]
    timeline_revenue = [round(x[1]["revenue"], 2) for x in daily_sorted]
    timeline_profit = [round(x[1]["profit"], 2) for x in daily_sorted]
    timeline_units = [x[1]["units"] for x in daily_sorted]

    # --- Category Breakdown ---
    cat_summary = {}
    for d in filtered:
        c = d["category"]
        if c not in cat_summary:
            cat_summary[c] = {"revenue": 0, "profit": 0, "units": 0, "customers": 0, "returns": 0, "days": 0}
        cat_summary[c]["revenue"] += d["revenue"]
        cat_summary[c]["profit"] += d["profit"]
        cat_summary[c]["units"] += d["units"]
        cat_summary[c]["customers"] += d["customers"]
        cat_summary[c]["returns"] += d["returns"]
        cat_summary[c]["days"] += 1

    table_rows = []
    for c, v in cat_summary.items():
        margin = (v["profit"] / v["revenue"] * 100) if v["revenue"] else 0
        table_rows.append({
            "category": c,
            "revenue": round(v["revenue"], 2),
            "profit": round(v["profit"], 2),
            "margin": round(margin, 1),
            "units": v["units"],
            "customers": v["customers"],
            "returns": v["returns"]
        })
    table_rows.sort(key=lambda x: x["revenue"], reverse=True)

    cat_labels = [r["category"] for r in table_rows]
    cat_revenue = [r["revenue"] for r in table_rows]
    cat_profit = [r["profit"] for r in table_rows]

    return jsonify({
        "kpis": {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "total_units": total_units,
            "total_customers": total_customers,
            "total_returns": total_returns,
            "avg_margin": round(avg_margin, 1)
        },
        "timeline": {
            "labels": timeline_labels,
            "revenue": timeline_revenue,
            "profit": timeline_profit,
            "units": timeline_units
        },
        "category": {
            "labels": cat_labels,
            "revenue": cat_revenue,
            "profit": cat_profit
        },
        "table": table_rows
    })


@app.route("/api/categories")
def api_categories():
    return jsonify({"categories": CATEGORIES})


HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Analytics Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d2e;
    --surface2: #252840;
    --border: #2e3155;
    --accent: #6c63ff;
    --accent2: #00d4aa;
    --accent3: #ff6b6b;
    --accent4: #ffd166;
    --text: #e8eaf6;
    --text-muted: #8b8fa8;
    --success: #00d4aa;
    --warning: #ffd166;
    --danger: #ff6b6b;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; }

  /* Header */
  .header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    position: sticky; top: 0; z-index: 100;
  }
  .logo { display: flex; align-items: center; gap: 10px; }
  .logo-icon { width: 36px; height: 36px; background: var(--accent); border-radius: 10px;
    display: flex; align-items: center; justify-content: center; font-size: 18px; }
  .logo-text { font-size: 1.1rem; font-weight: 700; letter-spacing: 0.5px; }
  .header-right { display: flex; align-items: center; gap: 12px; }
  .refresh-btn {
    background: var(--accent); color: #fff; border: none; padding: 8px 18px;
    border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600;
    transition: opacity .2s; display: flex; align-items: center; gap: 6px;
  }
  .refresh-btn:hover { opacity: 0.85; }
  .refresh-btn.loading { opacity: 0.6; pointer-events: none; }

  /* Filters */
  .filters-bar {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 1rem 2rem;
    display: flex; flex-wrap: wrap; gap: 1rem; align-items: flex-end;
  }
  .filter-group { display: flex; flex-direction: column; gap: 4px; }
  .filter-group label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .filter-group input, .filter-group select {
    background: var(--surface2); border: 1px solid var(--border); color: var(--text);
    padding: 8px 12px; border-radius: 8px; font-size: 0.875rem;
    outline: none; transition: border-color .2s;
  }
  .filter-group input:focus, .filter-group select:focus { border-color: var(--accent); }
  .cat-checkboxes { display: flex; flex-wrap: wrap; gap: 6px; }
  .cat-pill {
    display: flex; align-items: center; gap: 5px;
    background: var(--surface2); border: 1px solid var(--border);
    padding: 5px 12px; border-radius: 20px; cursor: pointer;
    font-size: 0.8rem; transition: all .2s; user-select: none;
  }
  .cat-pill input { display: none; }
  .cat-pill.active { background: var(--accent); border-color: var(--accent); color: #fff; }
  .cat-pill:hover:not(.active) { border-color: var(--accent); color: var(--accent); }

  /* Main */
  .main { padding: 2rem; max-width: 1600px; margin: 0 auto; }

  /* KPI Cards */
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
  .kpi-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.25rem 1.5rem;
    display: flex; flex-direction: column; gap: 8px;
    transition: transform .2s, box-shadow .2s;
    position: relative; overflow: hidden;
  }
  .kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--kpi-color, var(--accent));
  }
  .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,.3); }
  .kpi-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-value { font-size: 1.75rem; font-weight: 700; }
  .kpi-icon { position: absolute; right: 1rem; top: 50%; transform: translateY(-50%); font-size: 2rem; opacity: 0.1; }

  /* Charts */
  .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1rem; margin-bottom: 1rem; }
  .charts-row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
  .chart-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.5rem;
  }
  .chart-card h3 { font-size: 0.9rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.5px; margin-bottom: 1rem; display: flex; align-items: center; gap: 8px; }
  .chart-card h3 span { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); display: inline-block; }
  .chart-wrap { position: relative; }

  /* Table */
  .table-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; overflow: hidden; margin-bottom: 2rem;
  }
  .table-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between; }
  .table-header h3 { font-size: 0.9rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
  thead th {
    padding: 10px 16px; text-align: left;
    background: var(--surface2); color: var(--text-muted);
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
    cursor: pointer; user-select: none; white-space: nowrap;
  }
  thead th:hover { color: var(--text); }
  thead th .sort-arrow { margin-left: 4px; opacity: 0.5; }
  tbody tr { border-bottom: 1px solid var(--border); transition: background .15s; }
  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: var(--surface2); }
  tbody td { padding: 12px 16px; white-space: nowrap; }
  .badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
  }
  .badge-cat { background: rgba(108,99,255,.2); color: var(--accent); }
  .margin-bar { display: flex; align-items: center; gap: 8px; }
  .bar-bg { background: var(--surface2); border-radius: 4px; height: 6px; flex: 1; min-width: 60px; }
  .bar-fill { height: 100%; border-radius: 4px; background: var(--accent2); transition: width .5s; }

  /* Loading overlay */
  .loading-overlay {
    position: fixed; inset: 0; background: rgba(15,17,23,.7);
    display: flex; align-items: center; justify-content: center;
    z-index: 999; opacity: 0; pointer-events: none; transition: opacity .3s;
  }
  .loading-overlay.show { opacity: 1; pointer-events: all; }
  .spinner { width: 44px; height: 44px; border: 3px solid var(--border);
    border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Toast */
  .toast {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--surface2); border: 1px solid var(--border);
    padding: 12px 20px; border-radius: 10px; font-size: 0.875rem;
    transform: translateY(80px); opacity: 0; transition: all .3s;
    z-index: 200;
  }
  .toast.show { transform: translateY(0); opacity: 1; }

  /* Responsive */
  @media (max-width: 900px) {
    .charts-grid { grid-template-columns: 1fr; }
    .charts-row2 { grid-template-columns: 1fr; }
    .header { padding: 0 1rem; }
    .filters-bar { padding: 1rem; }
    .main { padding: 1rem; }
  }
</style>
</head>
<body>

<div class="loading-overlay" id="loadingOverlay"><div class="spinner"></div></div>
<div class="toast" id="toast"></div>

<header class="header">
  <div class="logo">
    <div class="logo-icon">📊</div>
    <span class="logo-text">MetricsPulse</span>
  </div>
  <div class="header-right">
    <span id="lastUpdated" style="font-size:.8rem;color:var(--text-muted)"></span>
    <button class="refresh-btn" onclick="loadData()">🔄 Refresh</button>
  </div>
</header>

<div class="filters-bar">
  <div class="filter-group">
    <label>Start Date</label>
    <input type="date" id="startDate" value="2024-01-01">
  </div>
  <div class="filter-group">
    <label>End Date</label>
    <input type="date" id="endDate" value="2024-03-31">
  </div>
  <div class="filter-group">
    <label>Quick Range</label>
    <select id="quickRange" onchange="applyQuickRange()">
      <option value="">Custom</option>
      <option value="Q1">Q1 2024</option>
      <option value="Q2">Q2 2024</option>
      <option value="Q3">Q3 2024</option>
      <option value="Q4">Q4 2024</option>
      <option value="H1">H1 2024</option>
      <option value="H2">H2 2024</option>
      <option value="FULL">Full Year 2024</option>
    </select>
  </div>
  <div class="filter-group">
    <label>Categories</label>
    <div class="cat-checkboxes" id="catCheckboxes"></div>
  </div>
  <div class="filter-group" style="justify-content:flex-end">
    <button class="refresh-btn" onclick="loadData()">Apply Filters</button>
  </div>
</div>

<main class="main">
  <!-- KPIs -->
  <div class="kpi-grid">
    <div class="kpi-card" style="--kpi-color:#6c63ff">
      <div class="kpi-label">Total Revenue</div>
      <div class="kpi-value" id="kpiRevenue">—</div>
      <div class="kpi-icon">💰</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#00d4aa">
      <div class="kpi-label">Total Profit</div>
      <div class="kpi-value" id="kpiProfit">—</div>
      <div class="kpi-icon">📈</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#ffd166">
      <div class="kpi-label">Avg Margin</div>
      <div class="kpi-value" id="kpiMargin">—</div>
      <div class="kpi-icon">%</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#ff9f43">
      <div class="kpi-label">Units Sold</div>
      <div class="kpi-value" id="kpiUnits">—</div>
      <div class="kpi-icon">📦</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#a29bfe">
      <div class="kpi-label">Customers</div>
      <div class="kpi-value" id="kpiCustomers">—</div>
      <div class="kpi-icon">👥</div>
    </div>
    <div class="kpi-card" style="--kpi-color:#ff6b6b">
      <div class="kpi-label">Returns</div>
      <div class="kpi-value" id="kpiReturns">—</div>
      <div class="kpi-icon">↩️</div>
    </div>
  </div>

  <!-- Main Charts -->
  <div class="charts-grid">
    <div class="chart-card">
      <h3><span style="background:#6c63ff"></span>Revenue & Profit Over Time</h3>
      <div class="chart-wrap"><canvas id="timelineChart" height="100"></canvas></div>
    </div>
    <div class="chart-card">
      <h3><span style="background:#00d4aa"></span>Revenue by Category</h3>
      <div class="chart-wrap"><canvas id="donutChart" height="200"></canvas></div>
    </div>
  </div>

  <div class="charts-row2">
    <div class="chart-card">
      <h3><span style="background:#ffd166"></span>Category Revenue vs Profit</h3>
      <div class="chart-wrap"><canvas id="barChart" height="120"></canvas></div>
    </div>
    <div class="chart-card">
      <h3><span style="background:#ff9f43"></span>Units Sold Over Time</h3>
      <div class="chart-wrap"><canvas id="unitsChart" height="120"></canvas></div>
    </div>
  </div>

  <!-- Summary Table -->
  <div class="table-card">
    <div class="table-header">
      <h3>📋 Category Summary</h3>
      <span style="font-size:.8rem;color:var(--text-muted)" id="tableCount"></span>
    </div>
    <div class="table-wrap">
      <table id="summaryTable">
        <thead>
          <tr>
            <th onclick="sortTable('category')">Category <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable('revenue')">Revenue <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable('profit')">Profit <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable('margin')">Margin <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable('units')">Units <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable('customers')">Customers <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable('returns')">Returns <span class="sort-arrow">↕</span></th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>
</main>

<script>
const PALETTE = ['#6c63ff','#00d4aa','#ffd166','#ff6b6b','#ff9f43','#a29bfe','#fd79a8'];
let charts = {};
let tableData = [];
let sortKey = 'revenue', sortAsc = false;

const chartDefaults = {
  responsive: true,
  plugins: { legend: { labels: { color: '#8b8fa8', font: { size: 12 } } } },
  scales: {
    x: { ticks: { color: '#8b8fa8', font: { size: 10 }, maxTicksLimit: 10 }, grid: { color: '#2e3155' } },
    y: { ticks: { color: '#8b8fa8', font: { size: 11 } }, grid: { color: '#2e3155' } }
  }
};

function fmt(n) {
  if (n >= 1e6) return '$' + (n/1e6).toFixed(2) + 'M';
  if (n >= 1e3) return '$' + (n/1e3).toFixed(1) + 'K';
  return '$' + n.toFixed(2);
}
function fmtNum(n) {
  return n >= 1e3 ? (n/1e3).toFixed(1) + 'K' : n.toString();
}

async function loadData() {
  const btn = document.querySelector('.refresh-btn');
  const overlay = document.getElementById('loadingOverlay');
  overlay.classList.add('show');

  const start = document.getElementById('startDate').value;
  const end = document.getElementById('endDate').value;
  const cats = getSelectedCats();

  if (!start || !end || start > end) {
    showToast('⚠️ Please select a valid date range');
    overlay.classList.remove('show');
    return;
  }

  const params = new URLSearchParams({ start, end });
  cats.forEach(c => params.append('categories', c));

  try {
    const res = await fetch('/api/metrics?' + params);
    const d = await res.json();
    updateKPIs(d.kpis);
    updateTimeline(d.timeline);
    updateDonut(d.category);
    updateBar(d.category);
    updateUnits(d.timeline);
    tableData = d.table;
    renderTable();
    document.getElementById('lastUpdated').textContent = 'Updated ' + new Date().toLocaleTimeString();
    showToast('✅ Data refreshed');
  } catch(e) {
    showToast('❌ Failed to load data');
  } finally {
    overlay.classList.remove('show');
  }
}

function updateKPIs(k) {
  document.getElementById('kpiRevenue').textContent = fmt(k.total_revenue);
  document.getElementById('kpiProfit').textContent = fmt(k.total_profit);
  document.getElementById('kpiMargin').textContent = k.avg_margin + '%';
  document.getElementById('kpiUnits').textContent = fmtNum(k.total_units);
  document.getElementById('kpiCustomers').textContent = fmtNum(k.total_customers);
  document.getElementById('kpiReturns').textContent = k.total_returns.toLocaleString();
}

function updateTimeline(t) {
  if (charts.timeline) charts.timeline.destroy();
  const ctx = document.getElementById('timelineChart').getContext('2d');
  charts.timeline = new Chart(ctx, {
    type: 'line',
    data: {
      labels: t.labels,
      datasets: [
        {
          label: 'Revenue',
          data: t.revenue,
          borderColor: '#6c63ff',
          backgroundColor: 'rgba(108,99,255,.12)',
          fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2
        },
        {
          label: 'Profit',
          data: t.profit,
          borderColor: '#00d4aa',
          backgroundColor: 'rgba(0,212,170,.08)',
          fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2
        }
      ]
    },
    options: {
      ...chartDefaults,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        ...chartDefaults.plugins,
        tooltip: {
          callbacks: {
            label: ctx => ctx.dataset.label + ': ' + fmt(ctx.raw)
          }
        }
      }
    }
  });
}

function updateDonut(c) {
  if (charts.donut) charts.donut.destroy();
  const ctx = document.getElementById('donutChart').getContext('2d');
  charts.donut = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: c.labels,
      datasets: [{ data: c.revenue, backgroundColor: PALETTE, borderWidth: 2, borderColor: '#1a1d2e' }]
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { color: '#8b8fa8', padding: 12, font: { size: 11 } } },
        tooltip: { callbacks: { label: ctx => ctx.label + ': ' + fmt(ctx.raw) } }
      }
    }
  });
}

function updateBar(c) {
  if (charts.bar) charts.bar.destroy();
  const ctx = document.getElementById('barChart').getContext('2d');
  charts.bar = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: c.labels,
      datasets: [
        { label: 'Revenue', data: c.revenue, backgroundColor: 'rgba(108,99,255,.8)', borderRadius: 6 },
        { label: 'Profit', data: c.profit, backgroundColor: 'rgba(0,212,170,.8)', borderRadius: 6 }
      ]
    },
    options: {
      ...chartDefaults,
      plugins: {
        ...chartDefaults.plugins,
        tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + fmt(ctx.raw) } }
      }
    }
  });
}

function updateUnits(t) {
  if (charts.units) charts.units.destroy();
  const ctx = document.getElementById('unitsChart').getContext('2d');
  charts.units = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: t.labels,
      datasets: [{
        label: 'Units', data: t.units,
        backgroundColor: 'rgba(255,154,67,.7)',
        borderRadius: 2
      }]
    },
    options: { ...chartDefaults }
  });
}

function renderTable() {
  const sorted = [...tableData].sort((a, b) => {
    const v = sortAsc ? 1 : -1;
    return typeof a[sortKey] === 'string'
      ? v * a[sortKey].localeCompare(b[sortKey])
      : v * (a[sortKey] - b[sortKey]);
  });
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = sorted.map((r, i) => `
    <tr>
      <td><span class="badge badge-cat">${r.category}</span></td>
      <td><strong>${fmt(r.revenue)}</strong></td>
      <td>${fmt(r.profit)}</td>
      <td>
        <div class="margin-bar">
          <div class="bar-bg"><div class="bar-fill" style="width:${Math.min(r.margin, 100)}%"></div></div>
          <span>${r.margin}%</span>
        </div>
      </td>
      <td>${r.units.toLocaleString()}</td>
      <td>${r.customers.toLocaleString()}</td>
      <td style="color:var(--danger)">${r.returns}</td>
    </tr>
  `).join('');
  document.getElementById('tableCount').textContent = sorted.length + ' categories';
}

function sortTable(key) {
  if (sortKey === key) sortAsc = !sortAsc; else { sortKey = key; sortAsc = false; }
  renderTable();
}

function getSelectedCats() {
  return [...document.querySelectorAll('.cat-pill.active')].map(p => p.dataset.cat);
}

function applyQuickRange() {
  const v = document.getElementById('quickRange').value;
  const ranges = {
    Q1: ['2024-01-01','2024-03-31'], Q2: ['2024-04-01','2024-06-30'],
    Q3: ['2024-07-01','2024-09-30'], Q4: ['2024-10-01','2024-12-31'],
    H1: ['2024-01-01','2024-06-30'], H2: ['2024-07-01','2024-12-31'],
    FULL: ['2024-01-01','2024-12-31']
  };
  if (ranges[v]) {
    document.getElementById('startDate').value = ranges[v][0];
    document.getElementById('endDate').value = ranges[v][1];
    loadData();
  }
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

async function initCategories() {
  const res = await fetch('/api/categories');
  const d = await res.json();
  const container = document.getElementById('catCheckboxes');
  d.categories.forEach((cat, i) => {
    const pill = document.createElement('label');
    pill.className = 'cat-pill active';
    pill.dataset.cat = cat;
    pill.innerHTML = `<input type="checkbox" checked> ${cat}`;
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      pill.classList.toggle('active');
      document.getElementById('quickRange').value = '';
    });
    container.appendChild(pill);
  });
}

(async () => {
  await initCategories();
  await loadData();
})();
</script>
</body>
</html>
'''


@app.route("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    import uvicorn
    # Use werkzeug directly for Flask
    app.run(host="0.0.0.0", port=3000, debug=False)
