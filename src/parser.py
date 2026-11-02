from __future__ import annotations

import json
import os

from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from dotenv import load_dotenv
from bs4 import BeautifulSoup

from models import Vacancy
from cleaning import (
    normalize_currency,
    normalize_skill,
    parse_salary,
    clean_description,
    extract_skills,
)


load_dotenv()

BASE_URL = os.getenv("BASE_URL")


def _make_soup(html: str) -> BeautifulSoup:
    """Create a BeautifulSoup object from raw HTML."""
    return BeautifulSoup(html, "lxml")


def parse_list_page(html: str) -> list[str]:
    """Extract vacancy IDs from an HTML listing page."""
    soup = _make_soup(html)
    links = soup.select("a.vacancy-card__backdrop-link")

    return [link["href"].split("/")[-1] for link in links]


def parse_vacancy_page(html: str) -> Vacancy:
    """Extract structured vacancy data from an HTML page."""
    soup = _make_soup(html)

    # Extract the vacancy data stored in the page's SSR state.
    tag = soup.select_one("script[data-ssr-state]")

    if tag is None:
        raise ValueError("script[data-ssr-state] not found")

    data = json.loads(tag.string)["vacancy"]

    # Extract nested objects and lists.
    company = data.get("company") or {}
    salary = data.get("salary") or {}
    predicted = data.get("predictedSalary") or {}
    published = data.get("publishedDate") or {}
    locations = data.get("locations") or []

    # Clean the description before extracting additional skills.
    description = clean_description(data.get("description"))

    # Combine skills from the structured JSON data and vacancy description.
    json_skills = [
        normalize_skill(skill["title"])
        for skill in data.get("skills") or []
    ]

    description_skills = extract_skills(description)

    # Remove duplicate skills while preserving their original order.
    skills = list(dict.fromkeys(json_skills + description_skills))

    return Vacancy(
        # Required fields: missing values indicate an invalid vacancy record.
        vacancy_id=data["id"],
        url=urljoin(BASE_URL, data["href"]),
        title=data["title"].strip(),

        # Optional fields: return None when the corresponding value is missing.
        company=company.get("title"),
        grade=data.get("qualification"),
        city=locations[0]["title"] if locations else None,
        employment=data.get("employment"),
        is_remote=data.get("remoteWork"),

        # Normalize salary values and currency codes.
        salary_from=parse_salary(salary.get("from")),
        salary_to=parse_salary(salary.get("to")),
        salary_currency=normalize_currency(salary.get("currency")),

        # Estimated salary provided by the website's salary calculator.
        predicted_salary_from=parse_salary(predicted.get("from")),
        predicted_salary_to=parse_salary(predicted.get("to")),

        published_at=published.get("date"),
        skills=skills,
        description=description,
        scraped_at=datetime.now().isoformat(timespec="seconds"),
    )


if __name__ == "__main__":
    # Quick test using a locally saved vacancy page: python src/parser.py
    path = (
        Path(__file__).resolve().parent.parent
        / "tests"
        / "test_vacancy1.html"
    )

    html = path.read_text(encoding="utf-8")
    print(parse_vacancy_page(html))