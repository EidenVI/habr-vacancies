from pathlib import Path
import sys
import os

from dotenv import load_dotenv
from fake_headers import Headers

load_dotenv()

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fetcher import get_html
from parser import parse_list_page, parse_vacancy_page
from models import Vacancy
from storage import init_db, upsert_vacancy, export_csv


URL_TEMPLATE = os.getenv("URL_TEMPLATE")
URL_ANALYTICS_TEMPLATE = os.getenv("URL_ANALYTICS_TEMPLATE")
VACANCY_URL_TEMPLATE = os.getenv("VACANCY_URL_TEMPLATE")

MAX_PAGES = int(os.getenv("MAX_PAGES"))

CSV_REL_PATH = os.getenv("OUTPUT_CSV_PATH")
CSV_FILE_PATH = BASE_DIR / CSV_REL_PATH


def run() -> None:
    headers = Headers().generate()

    listings_dir = BASE_DIR / "data" / "raw" / "listings"
    vacancies_dir = BASE_DIR / "data" / "raw" / "vacancies"

    vacancies: list[Vacancy] = []
    skipped: list[int] = []

    for page_number in range(1, MAX_PAGES + 1):
        # Change the URL template to collect vacancies from another job category.
        url = URL_ANALYTICS_TEMPLATE.format(page=page_number)

        file_path = listings_dir / f"page_{page_number:04d}.html"
        path = get_html(url=url, headers=headers, file_path=file_path)

        if path is None:
            print(f"Skipping page {page_number}: download failed")
            continue

        html = path.read_text(encoding="utf-8")
        vacancy_ids = parse_list_page(html=html)

        # Stop collecting when the listing page contains no vacancies.
        if not vacancy_ids:
            break

        for vacancy_id in vacancy_ids:
            # Build the URL of an individual vacancy page using its ID.
            # Example: https://career.habr.com/vacancies/1000169511
            vacancy_url = VACANCY_URL_TEMPLATE.format(vacancy_id=vacancy_id)

            vacancy_file = vacancies_dir / f"vacancy_{vacancy_id}.html"
            vacancy_path = get_html(
                url=vacancy_url,
                headers=headers,
                file_path=vacancy_file
            )

            if vacancy_path is None:
                print(f"Skipping vacancy {vacancy_id}: download failed")
                continue

            vacancy_html = vacancy_path.read_text(encoding="utf-8")

            try:
                vacancy = parse_vacancy_page(html=vacancy_html)
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                print(f"Skipping vacancy {vacancy_id}: {type(e).__name__}: {e}")
                skipped.append(vacancy_id)
                continue

            vacancies.append(vacancy)

            print("Parsed: {N}, skipped: {M}".format(N=len(vacancies), M=len(skipped)))

    # Initialize the database before inserting vacancy records.
    init_db()

    # Save collected vacancies to the database.
    for vacancy in vacancies:
        upsert_vacancy(vacancy)

    # Export the database contents to CSV for further analysis.
    export_csv(CSV_FILE_PATH)


if __name__ == "__main__":
    run()