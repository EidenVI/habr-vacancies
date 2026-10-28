import requests
from pathlib import Path

url = "https://career.habr.com/vacancies/1000169524"
response = requests.get(url=url, timeout=10)
response.raise_for_status()

file_path = Path("tests/test_vacancy1.html")
file_path.parent.mkdir(parents=True, exist_ok=True)
file_path.write_bytes(response.content)