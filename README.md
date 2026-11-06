# MetricsPulse — Analytics Dashboard

A sleek, production-ready analytics dashboard built with Flask + Chart.js, featuring interactive charts, KPI cards, and a sortable summary table with date-range and category filters.

## Features

- **6 KPI Cards** — Revenue, Profit, Margin %, Units, Customers, Returns
- **4 Interactive Charts** (Chart.js)
  - Revenue & Profit over time (line)
  - Revenue by category (doughnut)
  - Revenue vs Profit by category (grouped bar)
  - Units sold over time (bar)
- **Filters** — Date range picker, quick-range selector (Q1–Q4, H1, H2, Full Year), category toggle pills
- **Sortable Summary Table** — click any column header to sort ascending/descending
- **Dark theme** with animated transitions
- **Health check** endpoint at `/health`

## Running Locally

```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:3000
```

## Running with Docker

```bash
docker build -t metricspulse .
docker run -p 3000:3000 metricspulse
# Visit http://localhost:3000
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard UI |
| `/health` | GET | Health check (`{"status":"ok"}`) |
| `/api/metrics` | GET | Filtered metrics data |
| `/api/categories` | GET | List of all categories |

### `/api/metrics` Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start` | date (YYYY-MM-DD) | `2024-01-01` | Start of date range |
| `end` | date (YYYY-MM-DD) | `2024-03-31` | End of date range |
| `categories` | string (repeatable) | all | Filter by category name |

**Example:**
```
GET /api/metrics?start=2024-01-01&end=2024-06-30&categories=Electronics&categories=Sports
```

## Project Structure

```
.
├── app.py            # Flask app — data generation, API routes, embedded HTML/CSS/JS
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container config (port 3000)
└── README.md
```

## Data

The dashboard uses procedurally generated synthetic sales data for the full year 2024 across 5 categories:
- Electronics, Clothing, Food & Beverage, Sports, Home & Garden

Data includes daily revenue, profit, units sold, customer counts, and return rates with realistic seasonal variation and noise.
