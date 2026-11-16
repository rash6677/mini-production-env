"""HTTP endpoints for the DRF employee service."""

from time import perf_counter

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter, Histogram, make_asgi_app

from app import database

app = FastAPI(title="DRF Employee API", version="0.1.0")

HTTP_REQUESTS = Counter(
    "drf_http_requests_total",
    "HTTP requests handled by the DRF API",
    ["method", "endpoint", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "drf_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


@app.middleware("http")
async def record_http_metrics(request: Request, call_next):
    """Record request count and duration using bounded route labels."""
    started_at = perf_counter()
    status = "500"
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        # Avoid counting Prometheus's own scrape traffic as user traffic.
        if not request.url.path.startswith("/metrics"):
            route = request.scope.get("route")
            endpoint = getattr(route, "path", request.url.path)
            labels = (request.method, endpoint)
            HTTP_REQUESTS.labels(*labels, status).inc()
            HTTP_REQUEST_DURATION.labels(*labels).observe(perf_counter() - started_at)


# Prometheus scrapes this ASGI sub-application at /metrics.
app.mount("/metrics", make_asgi_app())


@app.get("/")
def welcome() -> dict[str, str]:
    return {"message": "Welcome to the DRF Employee API"}


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def readiness() -> dict[str, str]:
    try:
        database.check_database()
    except Exception as error:
        raise HTTPException(status_code=503, detail="Database is unavailable") from error
    return {"status": "ready"}


@app.get("/employees")
def get_employees() -> list[dict[str, object]]:
    try:
        return database.list_employees()
    except Exception as error:
        raise HTTPException(status_code=503, detail="Employee data is unavailable") from error


@app.get("/employees/{employee_id}")
def get_employee(employee_id: int) -> dict[str, object]:
    try:
        employee = database.find_employee(employee_id)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Employee data is unavailable") from error
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee
