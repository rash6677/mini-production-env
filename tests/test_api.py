import pytest
from fastapi import HTTPException

from app import database
from app.main import get_employee, get_employees, liveness, readiness, welcome

SAMPLE_EMPLOYEES = [
    {"id": 1, "name": "Asha Rao", "role": "Platform Engineer", "department": "Engineering"},
    {"id": 2, "name": "Rohan Mehta", "role": "People Operations Specialist", "department": "People"},
]


def test_welcome_endpoint() -> None:
    assert "DRF" in welcome()["message"]


def test_liveness_does_not_require_database(monkeypatch) -> None:
    def database_must_not_be_called() -> None:
        raise AssertionError("liveness should not check PostgreSQL")

    monkeypatch.setattr(database, "check_database", database_must_not_be_called)
    assert liveness() == {"status": "alive"}


def test_readiness_reports_database_unavailable(monkeypatch) -> None:
    def unavailable() -> None:
        raise OSError("database is down")

    monkeypatch.setattr(database, "check_database", unavailable)
    with pytest.raises(HTTPException) as error:
        readiness()
    assert error.value.status_code == 503


def test_readiness_when_database_is_available(monkeypatch) -> None:
    monkeypatch.setattr(database, "check_database", lambda: None)
    assert readiness() == {"status": "ready"}


def test_list_employees(monkeypatch) -> None:
    monkeypatch.setattr(database, "list_employees", lambda: SAMPLE_EMPLOYEES)
    assert get_employees() == SAMPLE_EMPLOYEES


def test_get_one_employee(monkeypatch) -> None:
    monkeypatch.setattr(database, "find_employee", lambda employee_id: SAMPLE_EMPLOYEES[0])
    assert get_employee(1) == SAMPLE_EMPLOYEES[0]


def test_unknown_employee_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(database, "find_employee", lambda employee_id: None)
    with pytest.raises(HTTPException) as error:
        get_employee(999)
    assert error.value.status_code == 404


def test_employee_endpoint_reports_database_unavailable(monkeypatch) -> None:
    def unavailable() -> list[dict[str, object]]:
        raise OSError("database is down")

    monkeypatch.setattr(database, "list_employees", unavailable)
    with pytest.raises(HTTPException) as error:
        get_employees()
    assert error.value.status_code == 503
