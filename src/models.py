from dataclasses import asdict, dataclass


@dataclass
class Vacancy:
    id: str
    url: str
    title: str | None
    company: str | None
    salary_raw: str | None
    city: str | None
    employment: str | None
    grade: str | None
    skills: list[str]
    description: str | None
    published_at: str | None
    scraped_at: str

    def to_dict(self) -> dict:
        return asdict(self)
