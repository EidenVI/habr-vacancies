import time
from pathlib import Path

import requests


def get_html(url: str, headers: dict, file_path: Path) -> Path | None:
    """Скачивает HTML и сохраняет в file_path. Если файл уже есть — не качает заново."""
    file_path = Path(file_path)

    if file_path.exists():
        return file_path

    try:
        page = requests.get(url=url, headers=headers, timeout=10)
        page.raise_for_status()

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(page.content)

        time.sleep(1)
        return file_path

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the page: {e}")
        return None
