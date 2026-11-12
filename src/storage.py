import sqlite3
import json
import os

from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from models import Vacancy

load_dotenv()

CSV_REL_PATH = os.getenv("OUTPUT_CSV_PATH")
SQLITE_PATH = os.getenv("DATABASE_PATH")

BASE_DIR = Path(__file__).resolve().parent

# Tables exported to CSV for pandas and BI tools.
EXPORT_TABLES = ("vacancies", "vacancies_analytics", "skills", "vacancy_skills", "vacancy_queries")


def get_db_path() -> Path:
    """Resolve the database path and create its parent directory."""
    if not SQLITE_PATH:
        raise ValueError("DATABASE_PATH is not specified in .env")

    db_path = Path(SQLITE_PATH)

    if not db_path.is_absolute():
        db_path = BASE_DIR.parent / db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


@contextmanager
def _connect():
    """Open a connection with foreign keys enabled.

    SQLite ignores foreign keys (and ON DELETE CASCADE) unless the pragma is
    switched on for every new connection. The block commits on success, rolls
    back on error and always closes the connection.
    """
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database tables using the sqlite.sql file."""
    schema_path = BASE_DIR.parent / "sqlite.sql"

    with _connect() as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))

    print(f"Database initialized: {get_db_path()}")


def clean_db() -> None:
    """Delete all data from the database but keep the tables."""
    with _connect() as conn:
        # Children first, parents last.
        for table in ("vacancy_skills", "vacancy_queries", "skills", "vacancies"):
            conn.execute(f"DELETE FROM {table}")

        # Restart the AUTOINCREMENT counter of the skills table.
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'skills'")

    print("Database cleaned: all rows deleted")


def upsert_vacancy(vacancy: Vacancy) -> None:
    """Insert or update a vacancy and synchronize its skill relations."""
    vacancy_query = """
        INSERT INTO vacancies (
            vacancy_id, url, title, company, grade, city, employment,
            is_remote, salary_from, salary_to, salary_currency,
            predicted_salary_from, predicted_salary_to, published_at,
            description, scraped_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(vacancy_id) DO UPDATE SET
            url = excluded.url,
            title = excluded.title,
            company = excluded.company,
            grade = excluded.grade,
            city = excluded.city,
            employment = excluded.employment,
            is_remote = excluded.is_remote,
            salary_from = excluded.salary_from,
            salary_to = excluded.salary_to,
            salary_currency = excluded.salary_currency,
            predicted_salary_from = excluded.predicted_salary_from,
            predicted_salary_to = excluded.predicted_salary_to,
            published_at = excluded.published_at,
            description = excluded.description,
            scraped_at = excluded.scraped_at
    """

    values = (
        vacancy.vacancy_id,
        vacancy.url,
        vacancy.title,
        vacancy.company,
        vacancy.grade,
        vacancy.city,
        vacancy.employment,
        vacancy.is_remote,
        vacancy.salary_from,
        vacancy.salary_to,
        vacancy.salary_currency,
        vacancy.predicted_salary_from,
        vacancy.predicted_salary_to,
        vacancy.published_at,
        vacancy.description,
        vacancy.scraped_at,
    )

    skills = {s.strip().lower() for s in vacancy.skills if s and s.strip()}

    with _connect() as conn:
        # Upsert main vacancy record
        conn.execute(vacancy_query, values)

        # Reset existing skill links for idempotency
        conn.execute(
            "DELETE FROM vacancy_skills WHERE vacancy_id = ?",
            (vacancy.vacancy_id,),
        )

        # Ensure skills exist in the dictionary and link them to the vacancy
        for skill in skills:
            conn.execute("INSERT OR IGNORE INTO skills (name) VALUES (?)", (skill,))
            conn.execute(
                """
                INSERT INTO vacancy_skills (vacancy_id, skill_id)
                SELECT ?, skill_id FROM skills WHERE name = ?
                """,
                (vacancy.vacancy_id, skill),
            )


def export_csv(path: str | Path) -> None:
    """Export every table to CSV.

    `path` is the file for the vacancies table. The other tables are written
    next to it: skills.csv, vacancy_skills.csv and vacancy_queries.csv.
    """
    path = Path(path)

    if not path.is_absolute():
        path = BASE_DIR.parent / path

    out_dir = path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    with _connect() as conn:
        for table in EXPORT_TABLES:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)

            file_path = path if table == "vacancies" else out_dir / f"{table}.csv"

            df.to_csv(
                file_path,
                index=False,
                sep=";",
                encoding="utf-8-sig"
            )

            print(f"Exported {len(df)} rows from '{table}' to: {file_path}")


def save_csv(vacancies: list[Vacancy], path: str | Path) -> None:
    """Save a list of vacancy objects directly to a CSV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for vacancy in vacancies:
        row = vacancy.to_dict()

        # Serialize the skills list as JSON to store it in a single CSV cell.
        row["skills"] = json.dumps(
            row["skills"],
            ensure_ascii=False
        )

        rows.append(row)

    df = pd.DataFrame(rows)

    df.to_csv(
        path,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )

    print(f"Successfully saved {len(df)} vacancies to: {path}")