from pathlib import Path
import sys
from dotenv import load_dotenv
from fake_headers import Headers
import os

load_dotenv()

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fetcher import get_html
from parser import parse_list_page, parse_vacancy_page
from models import Vacancy
from storage import save_csv

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

    for page_number in range(1, MAX_PAGES + 1):
        # change me if you need another sphere
        url = URL_ANALYTICS_TEMPLATE.format(page=page_number)
        file_path = listings_dir / f"page_{page_number:04d}.html"
        path = get_html(url=url, headers=headers, file_path=file_path)

        if path is None:
            print(f"skip page {page_number}: download failed")
            continue

        html = path.read_text(encoding='utf-8')
        vacancy_ids = parse_list_page(html=html)

        if not vacancy_ids:
            break

        for vacancy_id in vacancy_ids:
            vacancy_url = VACANCY_URL_TEMPLATE.format(vacancy_id=vacancy_id) # https://career.habr.com/vacancies/1000169511

            vacancy_file = vacancies_dir / f"vacancy_{vacancy_id}.html"
            vacancy_path = get_html(url=vacancy_url, headers=headers, file_path=vacancy_file)

            if vacancy_path is None:
                print(f"skip vacancy {vacancy_id}: download failed")
                continue

            vacancy_html = vacancy_path.read_text(encoding="utf-8")
            vacancy = parse_vacancy_page(html=vacancy_html)
            vacancies.append(vacancy)
    
    save_csv(vacancies=vacancies, path=CSV_FILE_PATH)



if __name__ == "__main__":
    run()
