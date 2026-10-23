from pathlib import Path
import sys

from fake_headers import Headers

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fetcher import get_html

# Фильтры по специализациям лучше держать в .env; пока URL задан здесь.
URL_TEMPLATE = "https://career.habr.com/vacancies?page={page}&type=all"
MAX_PAGES = 1


def run() -> None:
    headers = Headers().generate()
    listings_dir = BASE_DIR / "data" / "raw" / "listings"

    for page_number in range(1, MAX_PAGES + 1):
        url = URL_TEMPLATE.format(page=page_number)
        file_path = listings_dir / f"page_{page_number:04d}.html"
        path = get_html(url=url, headers=headers, file_path=file_path)
        if path is None:
            print(f"skip page {page_number}: download failed")


if __name__ == "__main__":
    run()
