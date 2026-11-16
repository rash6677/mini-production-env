# DRF Employee API

A small FastAPI service used to learn application operations and SRE fundamentals.
Phase 1 includes the API and PostgreSQL access. Containerization and monitoring
are introduced in later phases.

## Phase 2: Docker Compose

Copy `.env.example` to `.env` and set a local development password. Compose reads
these settings so the password does not need to be written in the YAML file.
Build and start the API and PostgreSQL containers:

```powershell
docker compose up --build -d
docker compose ps
```

The API is published on `http://localhost:8001` in this environment because
host port 8000 is already in use. Inside Compose, the API still listens on 8000.
The database is reachable to the API as `db:5432` and is not published to the host.
Stop the services with `docker compose down`; the named database volume remains.

Phase 4 adds Prometheus at `http://localhost:9091` and Grafana at
`http://localhost:3001`. Grafana's local admin password is read from `.env`.
The API exposes Prometheus metrics at `/metrics`; Prometheus scrapes the internal
Compose address `app:8000`, and Grafana queries Prometheus at `prometheus:9090`.

The request counter is `drf_http_requests_total`, labeled with the HTTP method,
route template, and response status. The duration histogram is
`drf_http_request_duration_seconds`. The Python Prometheus client also exports
process CPU and resident memory series. Prometheus's `up{job="drf-api"}` series
shows whether its scrape of the API succeeded; it is not a complete user-facing
availability measurement.

The dashboard is provisioned from
`monitoring/grafana/dashboards/drf-overview.json`. It includes request rate,
p95 latency, response rates by status, 5xx percentage, scrape availability,
process CPU, and process memory. Prometheus keeps seven days of local samples.

## Phase 5: GitHub Actions CI

The workflow at `.github/workflows/ci.yml` runs on every push and pull request.
It checks out the code, selects Python 3.12, installs `requirements.txt`, checks
Python syntax, runs Pytest, imports the FastAPI app, and builds the Docker image.
It does not publish or deploy the image and requires no credentials.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health/live` | Confirms that the API process can answer |
| GET | `/health/ready` | Confirms that PostgreSQL can answer |
| GET | `/employees` | Lists employee rows from PostgreSQL |
| GET | `/employees/{employee_id}` | Gets one employee; returns 404 if absent |

Database-backed endpoints return HTTP 503 when PostgreSQL is unavailable. The
database must be initialized before employee queries; initialization creates the
table and adds three sample rows if the table is empty.

## Local setup (Windows PowerShell)

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the listed Python dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Set `DATABASE_URL` for a PostgreSQL server listening on your computer. The
   example value in `.env.example` is a template, not a provisioned account:

   ```powershell
   $env:DATABASE_URL = "postgresql://postgres:YOUR_LOCAL_PASSWORD@localhost:5432/drf"
   ```

4. Initialize the database, then start the API:

   ```powershell
   python -m app.database
   python -m uvicorn app.main:app --reload
   ```

5. Open `http://localhost:8000/docs` for FastAPI's interactive API page.

## Tests

```powershell
python -m pytest -q
```

The tests replace the database functions with small fakes. This checks endpoint
behavior without requiring a running PostgreSQL service; use `/health/ready` to
check a real database connection.
