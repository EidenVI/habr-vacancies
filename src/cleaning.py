from bs4 import BeautifulSoup

def parse_salary(text: str | None):
    """Сырая строка зарплаты → числа / валюта. Не вызывать из fetcher/parser."""
    raise NotImplementedError


def normalize_skill(text: str) -> str:
    raise NotImplementedError

def clean_description(html: str | None) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)