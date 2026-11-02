import time
from pathlib import Path

import requests


def get_html(url: str, headers: dict, file_path: Path) -> Path | None:
    """Download an HTML page and save it locally. Reuse the file if it already exists."""
    file_path = Path(file_path)

    # Reuse the previously downloaded page to avoid unnecessary requests.
    if file_path.exists():
        return file_path

    try:
        page = requests.get(
            url=url,
            headers=headers,
            timeout=10
        )

        # Raise an exception if the server returns an unsuccessful HTTP status.
        page.raise_for_status()

        # Create the parent directory if it does not exist.
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the downloaded HTML content to a local file.
        file_path.write_bytes(page.content)

        # Pause between requests to reduce the load on the website.
        time.sleep(1)

        return file_path

    except requests.exceptions.RequestException as error:
        print(f"Error downloading the page: {error}")
        return None