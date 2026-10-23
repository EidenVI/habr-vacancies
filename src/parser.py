from models import Vacancy


def parse_list_page(html: str) -> list[str]:
    """HTML выдачи → список id вакансий."""
    raise NotImplementedError


def parse_vacancy_page(html: str) -> Vacancy:
    """HTML страницы вакансии → Vacancy."""
    raise NotImplementedError
