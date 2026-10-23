# Habr Career: сбор и анализ вакансий

Учебный проект по полному циклу работы аналитика: сбор сырых страниц, разбор HTML в структурированные записи, очистка, таблица и позже дашборд.

Этот файл — карта репозитория: **что лежит в каком файле, какие функции туда писать и кто кого вызывает.** Код парсера сюда не входит, только контракты и связи.

---

## Как это устроено одной фразой

`pipeline.py` ничего не парсит и ничего не качает сам. Он только вызывает остальные модули в нужном порядке.

```text
.env (ссылка с фильтрами)
        │
        ▼
 pipeline.run()
        │
        ├─ fetcher.get_html()          сеть → data/raw/*.html
        ├─ parser.parse_list_page()    HTML выдачи → список id
        ├─ parser.parse_vacancy_page() HTML вакансии → Vacancy
        ├─ storage.upsert_vacancy()    Vacancy → БД / JSONL
        └─ cleaning.parse_salary()     позже, не внутри цикла сбора
```

Правило слоёв:

| Модуль | Можно | Нельзя |
|---|---|---|
| `fetcher.py` | HTTP, пауза, сохранить файл | искать зарплату в DOM |
| `parser.py` | BeautifulSoup по строке HTML | ходить в сеть |
| `models.py` | описать поля вакансии | логика |
| `storage.py` | записать / прочитать запись | качать страницы |
| `cleaning.py` | «от 200 000 ₽» → число | зависеть от requests |
| `pipeline.py` | циклы и порядок вызовов | CSS-селекторы и SQL-детали |

Если Habr поменяет вёрстку, вы правите только `parser.py` и перечитываете уже скачанный HTML. Если поменяется ссылка фильтра — меняется `.env`, парсер об этом не знает.

---

## Дерево проекта

```text
habr-vacancies/
├── .env                  # HABR_BASE_URL, HABR_SEARCH_URL
├── README.md
├── requirements.txt
├── schema.sql            # схема БД, когда дойдёте до storage
├── data/
│   ├── raw/              # сырой HTML, не трогать руками
│   │   ├── listings/     # page_001.html, page_002.html, ...
│   │   └── vacancies/    # 1000169078.html
│   ├── processed/        # jsonl / sqlite после парсинга
│   └── filtered/         # очищенный датасет для анализа
├── notebooks/            # EDA и дашборды, не часть run()
├── tests/                # тесты parser на сохранённом HTML
└── src/
    ├── models.py
    ├── fetcher.py
    ├── parser.py
    ├── storage.py
    ├── cleaning.py
    └── pipeline.py       # точка входа
```

Пока часть папок пустая — это нормально. Их создаёт код при первом запуске (`file_path.parent.mkdir(...)` уже есть в `fetcher.py`).

---

## Поток данных

Два цикла. Не один.

```text
1) Цикл выдачи
   search_url, page=1,2,3,...
        get_html → listings/page_NNN.html
        parse_list_page → [id, id, ...]
        пока есть «следующая страница»

2) Цикл вакансий (по уникальным id)
        если vacancies/{id}.html уже есть — не качать заново
        get_html → vacancies/{id}.html
        parse_vacancy_page → Vacancy
        upsert_vacancy / дописать jsonl
```

С карточки выдачи берите только **id и URL**. Город, зарплата, навыки — со страницы вакансии. Иначе получите два источника правды.

Пагинацию не хардкодьте как `for page in range(1, 99)`. На выдаче Habr пагинатор обрезан. Надёжный способ: после разбора страницы спросить «есть ли next?» и остановиться, когда нет.

---

## `src/models.py` — контракт записи

Сейчас здесь dataclass `Vacancy`. Это не парсер и не база. Это ответ на вопрос «как выглядит одна вакансия в программе».

Поля, которые уже заведены:

| Поле | Зачем |
|---|---|
| `id` | ключ, имя файла, upsert |
| `url` | воспроизводимость |
| `title` | анализ названий |
| `company` | группировки |
| `salary_raw` | как на сайте, без арифметики |
| `city` | география |
| `employment` | офис / удалёнка / формат |
| `grade` | junior / middle / senior, если есть |
| `skills` | список строк |
| `description` | полный текст, для NLP позже |
| `published_at` | дата с сайта |
| `scraped_at` | когда вы это сняли |

Что писать сюда:

- при необходимости маленький метод `to_dict()` через уже импортированный `asdict`;
- не класть сюда BeautifulSoup и `requests`.

Кто использует: `parser` **создаёт** `Vacancy`, `storage` **сохраняет**, `pipeline` только **передаёт** объект дальше.

---

## `src/fetcher.py` — только сеть и диск

Сейчас здесь `get_html(url, headers, file_path) -> Path | None`. Это единственная функция, которой разрешено ходить в интернет.

### `get_html(url, headers, file_path)`

1. Если `file_path` уже существует — вернуть его (кэш / повторный запуск).
2. `requests.get` с timeout.
3. При ошибке сети — не ронять весь прогон, вернуть `None` (позже можно добавить 2–3 повтора на 429/5xx).
4. Записать байты в файл.
5. Пауза (`time.sleep`) — лучше вызывать из цикла в `pipeline`, но пока она стоит внутри функции, это допустимо.
6. Вернуть путь к файлу.

Что **не** писать в этот файл:

- `run()` — точка входа только в `pipeline.py`.
- селекторы `.vacancy-card`.
- создание `Vacancy`.

Кто вызывает: только `pipeline`.

---

## `src/parser.py` — HTML → структура

Сети нет. На вход — строка HTML или `Path` к уже скачанному файлу. На выход — либо список id, либо `Vacancy`.

Заготовки в комментарии файла:

### `parse_list_page(html: str) -> list[str]`

Разбирает страницу выдачи.

- Находит карточки (`div.vacancy-card` / `a.vacancy-card__backdrop-link`).
- Достаёт id из `/vacancies/1000169078`.
- Возвращает список уникальных id.
- Опционально рядом: `get_next_page_url(html, current_url) -> str | None` — ссылка «следующая» или `None`.

Не возвращайте отсюда полные объекты вакансий. Выдача беднее карточки вакансии.

### `parse_vacancy_page(html: str) -> Vacancy`

Разбирает одну страницу вакансии.

- Заполняет поля `Vacancy`.
- Если блока нет (нет зарплаты, нет города) — пишите `None`, не падайте.
- `scraped_at` можно проставить здесь или в `pipeline` через `datetime.now(UTC).isoformat()`.

Кто вызывает: `pipeline`, после того как `get_html` вернул путь. Типичный вызов:

```text
path = get_html(...)
html = path.read_text(encoding="utf-8")
vacancy = parse_vacancy_page(html)
```

Тесты пишите именно на этот модуль: подсовывайте `data/raw/test_page1.html` без интернета.

---

## `src/storage.py` — куда девать Vacancy

Комментарий в файле: `init_db()`, `upsert_vacancy()`, `export_csv()`.

Смысл: парсер не должен знать, SQLite у вас или JSONL. Он отдаёт объект, storage решает.

Практичный порядок для первого парсера:

1. **Сначала JSONL** — одна вакансия = одна строка в `data/processed/vacancies.jsonl`. Упал скрипт на 80-й — первые 79 живы.
2. **Потом SQLite**, когда поля стабилизируются. Тогда пригодится `schema.sql`.

### `init_db()`

Создать таблицу, если её нет. Вызывается один раз в начале `run()`.

### `upsert_vacancy(vacancy: Vacancy)`

Вставить или обновить по `id`. Повторный прогон не плодит дубликаты.

### `export_csv(path)` / `export_dataframe()`

Выгрузка для pandas и ноутбуков. Это мост к анализу, не часть парсинга DOM.

Кто вызывает: `pipeline` после каждого успешного `parse_vacancy_page`. Не копите 500 объектов в списке «потом запишем» — пишите сразу.

---

## `src/cleaning.py` — подготовка к анализу

Комментарий в файле: `parse_salary(text)`, `normalize_skill(text)`.

Это **не** этап сбора. Сбор кладёт `salary_raw="от 200 000 ₽"`. Очистка потом делает `salary_from=200000`, `currency="RUB"`.

### `parse_salary(text: str) -> ...`

Вытащить числа, «от/до», валюту. Если «не указана» — `None`.

### `normalize_skill(text: str) -> str`

`"Python "` и `"python"` → один навык.

Когда вызывать:

- либо отдельным проходом по уже сохранённым записям;
- либо в ноутбуке `01_clean.ipynb`;
- **не** внутри `get_html` и лучше не внутри `parse_vacancy_page`.

Иначе сломается принцип «перепарсил HTML заново, сырьё не поехало».

---

## `src/pipeline.py` — что сюда писать

Сейчас здесь `run()`: цикл по страницам выдачи и вызов `get_html`. `MAX_PAGES = 1`, пока парсер вакансий не готов. Сюда пишется **оркестрация**, не селекторы.

### Зачем файл существует

Чтобы `run()` читался как сценарий:

1. взять URL из `.env`;
2. обойти страницы выдачи;
3. собрать id;
4. обойти вакансии;
5. сохранить.

Если начнёте писать `soup.select(...)` в `pipeline.py` — вы смешали слои. Этот код принадлежит `parser.py`.

### Какие функции здесь логичны

#### `run(search_url: str | None = None) -> None`

Единственная точка входа. Если URL не передали — читает `HABR_SEARCH_URL` из `.env`.

Черновик порядка (это план, не готовый код):

```text
def run(search_url=None):
    url = search_url or os.getenv("HABR_SEARCH_URL")
    init_db()                          # storage

    ids = []
    page = 1
    while url:
        path = get_html(               # fetcher
            url,
            headers,
            RAW / "listings" / f"page_{page:03d}.html",
        )
        html = path.read_text(encoding="utf-8")
        ids.extend(parse_list_page(html))          # parser
        url = get_next_page_url(html, url)         # parser
        page += 1
        if MAX_PAGES and page > MAX_PAGES:         # для отладки
            break

    for vid in unique(ids):
        vpath = get_html(
            f"{BASE_URL}/vacancies/{vid}",
            headers,
            RAW / "vacancies" / f"{vid}.html",
        )
        vacancy = parse_vacancy_page(vpath.read_text(...))  # parser
        upsert_vacancy(vacancy)                    # storage
```

`if __name__ == "__main__": run()` — только в этом файле.

#### Необязательные помощники рядом с `run()`

Имеет смысл вынести, если `run()` разрастается:

| Функция | Делает |
|---|---|
| `collect_listing_ids(search_url) -> list[str]` | цикл 1 целиком |
| `collect_vacancies(ids) -> None` | цикл 2 целиком |

Это всё ещё pipeline: внутри них только вызовы fetcher/parser/storage.

### С чем pipeline связан, с чем нет

```text
pipeline ──► fetcher.get_html
        ──► parser.parse_list_page
        ──► parser.parse_vacancy_page
        ──► storage.init_db / upsert_vacancy
        ──► models.Vacancy   (только как тип, не создаёт руками)

pipeline ──✕ cleaning        (второй этап / ноутбук)
pipeline ──✕ notebooks
pipeline ──✕ CSS и SQL
```

`from models import Vacancy` в pipeline нужен, если аннотируете типы (`list[Vacancy]`). Создаёт вакансию parser, не pipeline.

### Как отлаживать, не качая весь каталог

В `.env` или константах pipeline:

- `MAX_PAGES=1`
- `MAX_VACANCIES=3`

Пока селекторы сырые, гоняйте одну выдачу и три вакансии. У вас уже есть `data/raw/test_page1.html` — на нём отлаживайте `parse_list_page` вообще без сети.

---

## `.env` и конфиг

Сейчас:

```env
habr_base_url = "https://career.habr.com/"
```

Имеет смысл явно:

```env
HABR_BASE_URL=https://career.habr.com
HABR_SEARCH_URL=https://career.habr.com/vacancies?s[]=98&s[]=41&...&type=all
REQUEST_DELAY=1
MAX_PAGES=1
MAX_VACANCIES=3
```

Фильтры Habr (`s[]=...`) — это просто query string. `parser` их не разбирает. Сменили направление аналитики — сменили URL, код тот же.

Отдельный `config.py` не обязателен, пока переменных мало. Когда их станет больше трёх — вынесите чтение env туда, а `pipeline` пусть принимает готовые значения.

---

## Что не класть в `run()`

Анализ, pandas-графики, Streamlit. Это следующий контур:

1. `python -m src.pipeline` → raw HTML + таблица/jsonl
2. `notebooks/01_clean.ipynb` → `cleaning.py` → датафрейм
3. `notebooks/02_eda.ipynb` → графики
4. дашборд читает уже очищенный csv/parquet

`schema.sql` заполняйте, когда поля `Vacancy` перестанут меняться каждую итерацию. До этого JSONL дешевле.

---

## Порядок реализации (чтобы не застрять)

1. Довести `get_html`: не качать файл, если он уже есть.
2. Написать `parse_list_page` по `data/raw/test_page1.html` (должно получиться 25 id).
3. Перенести `run()` в `pipeline.py`: одна страница выдачи, печать id, без вакансий.
4. Скачать 1–3 страницы вакансий через тот же `get_html`.
5. Написать `parse_vacancy_page` → объект `Vacancy`.
6. `storage`: дописывать jsonl.
7. Включить пагинацию и полный цикл.
8. Только потом `cleaning` и ноутбуки.

Не делайте шаг 8, пока шаг 5 не стабилен.

---

## Зависимости (ориентир для `requirements.txt`)

Уже используются в проекте: `requests`, `fake_headers`, `beautifulsoup4`, `lxml`, `pandas`.

Позже: `python-dotenv` для `.env`, если не хотите парсить файл вручную.

---

## Частые ошибки на старте

- Парсить выдачу как будто это полная вакансия.
- Качать вакансию отдельной функцией-клоном `get_html`. Вакансия — тот же `get_html`, другой путь файла.
- Хранить всё в `list` до конца и потерять прогресс при падении.
- Хардкодить URL фильтров внутри parser.
- Чистить зарплату в момент парсинга HTML.
- Писать селекторы в `pipeline.py`.

)