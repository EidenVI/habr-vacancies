def parse_salary(text: str | None):
    """Сырая строка зарплаты → числа / валюта. Не вызывать из fetcher/parser."""
    raise NotImplementedError


def normalize_skill(text: str) -> str:
    raise NotImplementedError
