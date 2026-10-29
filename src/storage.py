import sqlite3
import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from models import Vacancy


load_dotenv()

CSV_REL_PATH = os.getenv("OUTPUT_CSV_PATH")
SQLITE_PATH = os.getenv("DATABASE_PATH")

BASE_DIR = Path(__file__).resolve().parent


def init_db() -> None:
    """Создаёт таблицы базы данных по схеме schema.sql."""

    if not SQLITE_PATH:
        raise ValueError("DATABASE_PATH не указан в .env")

    db_path = Path(SQLITE_PATH)

    if not db_path.is_absolute():
        db_path = BASE_DIR.parent / db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = BASE_DIR / "schema.sql"

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))

    print(f"База данных инициализирована: {db_path}")


def upsert_vacancy(vacancy: Vacancy) -> None:
    """Добавляет вакансию или обновляет её, если она уже существует."""

    if not SQLITE_PATH:
        raise ValueError("DATABASE_PATH не указан в .env")

    db_path = Path(SQLITE_PATH)

    if not db_path.is_absolute():
        db_path = BASE_DIR.parent / db_path

    query = """
        INSERT INTO vacancies (
            vacancy_id,
            url,
            title,
            company,
            grade,
            city,
            employment,
            is_remote,
            salary_from,
            salary_to,
            salary_currency,
            predicted_salary_from,
            predicted_salary_to,
            published_at,
            skills,
            description,
            scraped_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

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
            skills = excluded.skills,
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
        json.dumps(vacancy.skills, ensure_ascii=False),
        vacancy.description,
        vacancy.scraped_at,
    )

    with sqlite3.connect(db_path) as conn:
        conn.execute(query, values)


def export_csv(path: str | Path) -> None:
    """Экспортирует все вакансии из SQLite в CSV."""

    if not SQLITE_PATH:
        raise ValueError("DATABASE_PATH не указан в .env")

    db_path = Path(SQLITE_PATH)

    if not db_path.is_absolute():
        db_path = BASE_DIR.parent / db_path

    path = Path(path)

    if not path.is_absolute():
        path = BASE_DIR.parent / path

    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM vacancies",
            conn
        )

    df.to_csv(
        path,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )

    print(f"Успешно экспортировано {len(df)} вакансий в: {path}")


def save_csv(vacancies: list[Vacancy], path: Path) -> None:
    """Сохраняет список вакансий в CSV."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for vacancy in vacancies:
        row = vacancy.__dict__.copy()

        # Сохраняем список навыков в CSV в виде JSON.
        if row.get("skills") is not None:
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

    print(f"Успешно сохранено {len(df)} вакансий в: {path}")