"""Small PostgreSQL access layer for the employee API."""

import os


def database_url() -> str:
    """Return the configured connection string or explain how to set it."""
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "DATABASE_URL is not set. Set it to a PostgreSQL connection string."
        )
    return value


def connect():
    """Open a connection; the caller is responsible for closing it."""
    # Import here so API endpoints and their unit tests can load without the
    # PostgreSQL driver installed. Real database operations still require it.
    import psycopg
    from psycopg.rows import dict_row

    return psycopg.connect(database_url(), row_factory=dict_row)


def initialize_database() -> None:
    """Create the employee table and insert sample rows if it is empty."""
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    department TEXT NOT NULL
                )
                """
            )
            cursor.execute("SELECT COUNT(*) AS total FROM employees")
            if cursor.fetchone()["total"] == 0:
                cursor.executemany(
                    "INSERT INTO employees (id, name, role, department) "
                    "VALUES (%s, %s, %s, %s)",
                    [
                        (1, "Asha Rao", "Platform Engineer", "Engineering"),
                        (2, "Rohan Mehta", "People Operations Specialist", "People"),
                        (3, "Mira Shah", "Site Reliability Engineer", "Engineering"),
                    ],
                )


def list_employees() -> list[dict[str, object]]:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, role, department FROM employees ORDER BY id"
            )
            return list(cursor.fetchall())


def find_employee(employee_id: int) -> dict[str, object] | None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, role, department FROM employees WHERE id = %s",
                (employee_id,),
            )
            return cursor.fetchone()


def check_database() -> None:
    """Raise an exception when PostgreSQL cannot answer a simple query."""
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized; sample employees are ready.")
