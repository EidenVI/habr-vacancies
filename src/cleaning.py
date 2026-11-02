from bs4 import BeautifulSoup
from pathlib import Path
import json
import re


# Load skill aliases from the external JSON dictionary.
# Add new variations to the JSON file instead of hardcoding them here.
SKILLS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "dictionaries"
    / "skills_dictionary.json"
)

with SKILLS_PATH.open("r", encoding="utf-8") as file:
    SKILL_DICTIONARY = json.load(file)


# Map alternative currency codes to their standard ISO codes.
CURRENCY_ALIASES = {
    "RUB": "RUB",
    "RUR": "RUB",
    "USD": "USD"
}


def extract_skills(description: str | None) -> list[str]:
    """Extract known skills from a vacancy description."""
    if not description:
        return []

    description = description.lower()
    found_skills = []

    for skill, variations in SKILL_DICTIONARY.items():
        for variation in variations:
            # Match complete words to avoid partial matches inside other words.
            pattern = rf"(?<!\w){re.escape(variation.lower())}(?!\w)"

            if re.search(pattern=pattern, string=description):
                found_skills.append(skill)
                break

    return found_skills


def normalize_currency(currency: str | None) -> str | None:
    """Convert currency codes to their standard representation."""
    if not currency:
        return None

    currency = currency.strip().upper()

    return CURRENCY_ALIASES.get(currency, currency)


def parse_salary(value: int | float | str | None) -> int | None:
    """Convert a raw salary value into an integer."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    # Remove whitespace and keep only numeric characters.
    value = value.replace(" ", "").replace("\xa0", "")
    digits = "".join(char for char in value if char.isdigit())

    return int(digits) if digits else None


def normalize_skill(text: str) -> str:
    """Remove unnecessary whitespace from a skill name."""
    return text.strip()


def clean_description(html: str | None) -> str:
    """Convert vacancy description HTML into plain text."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    return soup.get_text(separator="\n", strip=True)