CREATE TABLE IF NOT EXISTS vacancies (
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
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS vacancy_skills (
    vacancy_id INTEGER NOT NULL REFERENCES vacancies(vacancy_id) ON DELETE CASCADE,
    skill_id   INTEGER NOT NULL REFERENCES skills(skill_id) ON DELETE CASCADE,
    PRIMARY KEY (vacancy_id, skill_id)
);

CREATE TABLE IF NOT EXISTS vacancy_queries (
    vacancy_id INTEGER NOT NULL REFERENCES vacancies(vacancy_id) ON DELETE CASCADE,
    query      TEXT NOT NULL,
    PRIMARY KEY (vacancy_id, query)
);

CREATE INDEX IF NOT EXISTS idx_vacancy_skills_skill ON vacancy_skills(skill_id);

CREATE VIEW IF NOT EXISTS vacancies_analytics AS
SELECT
    v.*,
    CASE
        WHEN salary_from IS NOT NULL AND salary_to IS NOT NULL
            THEN (salary_from + salary_to) / 2.0
        WHEN salary_from IS NOT NULL THEN salary_from
        WHEN salary_to   IS NOT NULL THEN salary_to
    END AS salary_mid,
    CASE WHEN salary_from IS NOT NULL OR salary_to IS NOT NULL
         THEN 1 ELSE 0 END AS has_salary,
    substr(published_at, 1, 10) AS published_date
FROM vacancies v;