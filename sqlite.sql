CREATE TABLE vacancies (
    vacancy_id            INTEGER PRIMARY KEY,
    url                   TEXT NOT NULL,
    title                 TEXT NOT NULL,
    company               TEXT,
    grade                 TEXT,
    city                  TEXT,
    employment            TEXT,
    is_remote             INTEGER,
    salary_from           INTEGER,
    salary_to             INTEGER,
    salary_currency       TEXT,
    predicted_salary_from INTEGER,
    predicted_salary_to   INTEGER,
    published_at          TEXT,
    description           TEXT,
    scraped_at            TEXT NOT NULL

CREATE TABLE skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE
);

CREATE TABLE vacancy_skills (
    vacancy_id INTEGER NOT NULL REFERENCES vacancies(vacancy_id),
    skill_id   INTEGER NOT NULL REFERENCES skills(skill_id),
    PRIMARY KEY (vacancy_id, skill_id)
);

CREATE TABLE vacancy_queries (
    vacancy_id INTEGER NOT NULL REFERENCES vacancies(vacancy_id),
    query      TEXT NOT NULL,
    PRIMARY KEY (vacancy_id, query)
);

CREATE INDEX idx_vacancy_skills_skill ON vacancy_skills(skill_id);