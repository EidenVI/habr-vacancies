from pathlib import Path
import sys

from fake_headers import Headers

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fetcher import get_html
from parser import parse_list_page, parse_vacancy_page
from models import Vacancy

# Фильтры по специализациям лучше держать в .env; пока URL задан здесь.
URL_TEMPLATE = "https://career.habr.com/vacancies?page={page}&type=all"
VACANCY_URL_TEMPLATE = "https://career.habr.com/vacancies/{vacancy_id}"
MAX_PAGES = 256


def run() -> None:
    headers = Headers().generate()
    listings_dir = BASE_DIR / "data" / "raw" / "listings"
    vacancies_dir = BASE_DIR / "data" / "raw" / "vacancies"

    vacancies: list[Vacancy] = []

    for page_number in range(1, MAX_PAGES + 1):
        url = URL_TEMPLATE.format(page=page_number)
        file_path = listings_dir / f"page_{page_number:04d}.html"
        path = get_html(url=url, headers=headers, file_path=file_path)

        if path is None:
            print(f"skip page {page_number}: download failed")
            continue

        html = path.read_text(encoding='utf-8')
        vacancy_ids = parse_list_page(html=html)

        for vacancy_id in vacancy_ids:
            vacancy_url = VACANCY_URL_TEMPLATE.format(vacancy_id=vacancy_id) # https://career.habr.com/vacancies/1000169511

            vacancy_file = vacancies_dir / f"vacancy_{vacancy_id}.html"
            vacancy_path = get_html(url=vacancy_url, headers=headers, file_path=vacancy_file)

            if vacancy_path is None:
                print(f"skip vacancy {vacancy_id}: download failed")
                continue

            vacancy_html = path.read_text(encoding="utf-8")
            vacancy = parse_vacancy_page(html=vacancy_html)
            vacancies.append(vacancy)
    
    return vacancies



if __name__ == "__main__":
    run()
