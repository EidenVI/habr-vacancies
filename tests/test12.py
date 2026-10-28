import json
from pathlib import Path
from bs4 import BeautifulSoup

html = Path("tests/test_vacancy1.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "lxml")

tag = soup.select_one("script[data-ssr-state]")
print(type(tag))        # какой это объект

text = tag.string
print(text[:200])       # начало строки

data = json.loads(text)
print(data.keys())      # какие ключи есть на верхнем уровне

vacancy = data["vacancy"]
print(vacancy["title"])
print(vacancy["skills"])

Path("tests/vacancy.json").write_text(
    json.dumps(vacancy, ensure_ascii=False, indent=2), encoding="utf-8"
)