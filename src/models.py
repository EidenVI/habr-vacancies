from __future__ import annotations
from dataclasses import asdict, dataclass


@dataclass
class Vacancy:
    vacancy_id: int
    url: str
    title: str
    company: str | None
    grade: str | None
    city: str | None
    employment: str | None
    is_remote: bool | None
    salary_from: int | None
    salary_to: int | None
    salary_currency: str | None
    predicted_salary_from: int | None   # оценка калькулятора сайта, не зарплата из вакансии
    predicted_salary_to: int | None
    published_at: str | None
    skills: list[str]
    description: str | None
    scraped_at: str

    def to_dict(self) -> dict:
        return asdict(self)