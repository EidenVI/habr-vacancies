<div align="center">

Habr Career Analytics

A data analytics project based on job market data from Habr Career.

Collecting, processing, and analyzing IT job vacancies to explore labor market trends, in-demand skills, and salary distributions.

<br>
</div>

⸻

Overview

Habr Career Analytics is a Python-based project for collecting and analyzing job vacancy data from Habr Career.

The project implements a data pipeline that extracts vacancy information, parses structured data, normalizes fields, and stores the results in an SQLite database.

The collected dataset is intended for further exploratory data analysis (EDA) and visualization.

Project goals

* Collect job vacancies and their descriptions.
* Extract structured information, including salaries, locations, employment types, and skills.
* Normalize and clean collected data.
* Build a structured dataset for analytical purposes.
* Identify trends in the IT job market.
* Analyze salary distributions and demand for technical skills.

Architecture

flowchart TD
    A["Habr Career"] --> B["HTML Collection"]
    B --> C["Vacancy Parsing"]
    C --> D[("SQLite Database")]
    D --> E["Data Cleaning"]
    E --> F["Exploratory Data Analysis"]
    F --> G["Data Visualization"]
    style A fill:#E8F0FE,stroke:#4285F4,color:#174EA6
    style D fill:#E6F4EA,stroke:#34A853,color:#137333
    style F fill:#FFF4E5,stroke:#FBBC04,color:#8A4B08
    style G fill:#F3E8FD,stroke:#A142F4,color:#681DA8

Tech Stack

Category	Technologies
Language	Python
Data collection	Requests, BeautifulSoup4
HTML parsing	BeautifulSoup4, lxml
Data processing	Pandas
Database	SQLite
Data format	JSON
Configuration	python-dotenv

Project Structure

habr-career-analytics/
│
├── data/
│   ├── raw/
│   │   ├── listings/           # Downloaded vacancy listing pages
│   │   └── vacancies/          # Downloaded individual vacancy pages
│   │
│   ├── dictionaries/
│   │   └── skills_dictionary.json
│   │
│   └── processed/              # Processed datasets
│
├── src/
│   ├── fetcher.py              # HTML downloading
│   ├── parser.py               # Vacancy data extraction
│   ├── models.py               # Vacancy data model
│   ├── storage.py              # SQLite and CSV operations
│   ├── cleaning.py             # Data cleaning and normalization
│   ├── pipeline.py             # Main data pipeline
│   └── schema.sql              # Database schema
│
├── tests/
│   └── test_vacancy1.html      # Sample vacancy page
│
├── notebooks/                  # Exploratory data analysis
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

Getting Started

1. Clone the repository

git clone <REPOSITORY_URL>
cd habr-career-analytics

2. Create a virtual environment

python -m venv .venv

Activate it:

macOS / Linux

source .venv/bin/activate

Windows

.venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Create a .env file in the project root:

BASE_URL=https://career.habr.com
URL_ANALYTICS_TEMPLATE=https://career.habr.com/vacancies?page={page}
VACANCY_URL_TEMPLATE=https://career.habr.com/vacancies/{vacancy_id}
MAX_PAGES=10
DATABASE_PATH=data/vacancies.db
OUTPUT_CSV_PATH=data/processed/vacancies.csv

Adjust the listing URL to the search query or vacancy category you want to collect.

5. Run the pipeline

From the project root:

python src/pipeline.py

The pipeline downloads listing pages and individual vacancies, extracts structured information, stores records in SQLite, and exports the dataset to CSV.

Make sure the environment variables are configured and the export path is passed to export_csv() in the pipeline.

Data Processing

The project extracts and processes the following vacancy attributes:

Attribute	Description
Vacancy ID	Unique vacancy identifier
Title	Vacancy title
Company	Employer name
Grade	Required experience level
City	Job location
Employment	Employment type
Remote	Remote work availability
Salary	Salary range and currency
Predicted salary	Website salary estimate
Published at	Vacancy publication date
Skills	Structured and description-derived skills
Description	Cleaned vacancy description
Scraped at	Data collection timestamp

Skills are extracted from two sources:

* Structured data — skills provided directly by Habr Career.
* Vacancy description — additional skills identified using a custom dictionary of keywords and their variations.

Planned Features

* HTML collection
* Vacancy parsing
* SQLite storage with upsert support
* CSV export
* Salary and currency normalization
* Description cleaning
* Skill extraction using a custom dictionary
* Data quality checks
* Exploratory Data Analysis (EDA)
* Salary distribution analysis
* Skill demand analysis
* OLAP-style multidimensional analysis
* Interactive analytics dashboard

Dashboard

Coming soon.

An interactive dashboard will be added to explore vacancy statistics, salary distributions, and the demand for specific technologies and skills.

⸻

<div align="center">

Habr Career Analytics

Exploring the IT job market through data.

</div>
