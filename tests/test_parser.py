from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cleaning import description_to_text, normalize_skill, parse_salary, prepare_dataset
from parser import get_next_page_url, parse_list_meta, parse_list_page, parse_vacancy_page
from storage import export_csv, init_db, load_vacancies, upsert_vacancy


class ParserTests(unittest.TestCase):
    def test_parse_list_page(self) -> None:
        html = (ROOT / "data" / "raw" / "listings" / "test_page1.html").read_text(encoding="utf-8")
        ids = parse_list_page(html)
        self.assertEqual(len(ids), 25)
        self.assertTrue(all(item.isdigit() for item in ids))
        self.assertEqual(len(ids), len(set(ids)))

        meta = parse_list_meta(html)
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta["currentPage"], 1)
        self.assertGreaterEqual(meta["totalPages"], 2)
        next_url = get_next_page_url(html, "https://career.habr.com")
        self.assertIsNotNone(next_url)
        assert next_url is not None
        self.assertIn("page=2", next_url)

    def test_parse_vacancy_page(self) -> None:
        html = (ROOT / "tests" / "test_vacancy1.html").read_text(encoding="utf-8")
        vacancy = parse_vacancy_page(html)
        self.assertEqual(vacancy.vacancy_id, 1000169524)
        self.assertEqual(vacancy.company, "НЛМК ИТ")
        self.assertEqual(vacancy.grade, "Lead")
        self.assertEqual(vacancy.city, "Москва")
        self.assertTrue(vacancy.is_remote)
        self.assertIn("SQL", vacancy.skills)
        self.assertTrue(vacancy.title.startswith("Продуктовый аналитик"))
        self.assertIsNotNone(description_to_text(vacancy.description))


class StorageAndCleaningTests(unittest.TestCase):
    def test_upsert_and_dataset(self) -> None:
        html = (ROOT / "tests" / "test_vacancy1.html").read_text(encoding="utf-8")
        vacancy = parse_vacancy_page(html)
        tmp = ROOT / "tests" / "_tmp_vacancies.jsonl"
        filtered = ROOT / "tests" / "_tmp_filtered"
        try:
            if tmp.exists():
                tmp.unlink()
            init_db(tmp)
            upsert_vacancy(vacancy, tmp)
            upsert_vacancy(vacancy, tmp)
            rows = load_vacancies(tmp)
            self.assertEqual(len(rows), 1)
            csv_path = export_csv(path=ROOT / "tests" / "_tmp_vacancies.csv", source=tmp)
            self.assertTrue(csv_path.exists())
            vacancies_csv, skills_csv = prepare_dataset(source=tmp, dest_dir=filtered)
            self.assertTrue(vacancies_csv.exists())
            self.assertTrue(skills_csv.exists())
            self.assertGreaterEqual(skills_csv.read_text(encoding="utf-8").count("sql"), 1)
        finally:
            for path in (tmp, ROOT / "tests" / "_tmp_vacancies.csv"):
                if path.exists():
                    path.unlink()
            if filtered.exists():
                for item in filtered.iterdir():
                    item.unlink()
                filtered.rmdir()

    def test_parse_salary(self) -> None:
        self.assertEqual(parse_salary("от 200 000 до 300 000 ₽"), (200000, 300000, "RUB"))
        self.assertEqual(parse_salary("до 150 000 ₽"), (None, 150000, "RUB"))
        self.assertEqual(normalize_skill("  Python  "), "python")


if __name__ == "__main__":
    unittest.main()
