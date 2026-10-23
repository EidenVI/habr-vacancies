from models import Vacancy


def init_db() -> None:
    raise NotImplementedError


def upsert_vacancy(vacancy: Vacancy) -> None:
    raise NotImplementedError


def export_csv(path: str) -> None:
    raise NotImplementedError
