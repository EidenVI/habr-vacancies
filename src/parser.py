from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from dotenv import load_dotenv
import os

from bs4 import BeautifulSoup

from models import Vacancy
from cleaning import clean_description

load_dotenv()
BASE_URL = os.getenv('BASE_URL')


def _make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def parse_list_page(html: str) -> list[str]:
    """HTML выдачи -> список id вакансий."""
    soup = _make_soup(html)
    links = soup.select('a.vacancy-card__backdrop-link')

    return [link["href"].split("/")[-1] for link in links]


def parse_vacancy_page(html: str) -> Vacancy:
    """HTML страницы вакансии -> Vacancy."""
    soup = _make_soup(html)

    tag = soup.select_one("script[data-ssr-state]")
    if tag is None:
        raise ValueError("script[data-ssr-state] not found")
    data = json.loads(tag.string)["vacancy"]

    # Вложенные блоки могут быть None, поэтому `or {}` / `or []`:
    # без этого .get() на None упадёт с AttributeError.
    company = data.get("company") or {}
    salary = data.get("salary") or {}
    predicted = data.get("predictedSalary") or {}
    published = data.get("publishedDate") or {}
    locations = data.get("locations") or []

    return Vacancy(
        # обязательные поля: если их нет, карточка сломана, пусть упадёт сразу
        vacancy_id=data["id"],
        url=urljoin(BASE_URL, data["href"]),
        title=data["title"].strip(),
        # необязательные: .get() вернёт None, если ключа нет
        company=company.get("title"),
        grade=data.get("qualification"),
        city=locations[0]["title"] if locations else None,
        employment=data.get("employment"),
        is_remote=data.get("remoteWork"),
        salary_from=salary.get("from"),
        salary_to=salary.get("to"),
        salary_currency=salary.get("currency"),
        predicted_salary_from=predicted.get("from"),
        predicted_salary_to=predicted.get("to"),
        published_at=published.get("date"),
        skills=[skill["title"] for skill in data.get("skills") or []],
        description=clean_description(data.get("description")),
        scraped_at=datetime.now().isoformat(timespec="seconds"),
    )


if __name__ == "__main__":
    # быстрая проверка на сохранённой карточке: python src/parser.py
    path = Path(__file__).resolve().parent.parent / "tests" / "test_vacancy1.html"
    print(parse_vacancy_page(path.read_text(encoding="utf-8")))