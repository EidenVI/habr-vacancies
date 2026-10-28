from models import Vacancy
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

CSV_REL_PATH = os.getenv("OUTPUT_CSV_PATH")

def init_db() -> None:
    raise NotImplementedError


def upsert_vacancy(vacancy: Vacancy) -> None:
    raise NotImplementedError


def export_csv(path: str) -> None:
    raise NotImplementedError


def save_csv(vacancies: list[Vacancy], path: Path) -> None:
    df = pd.DataFrame([v.__dict__ for v in vacancies])

    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        path,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )

    print(f"Успешно сохранено {len(df)} вакансий в: {path}")