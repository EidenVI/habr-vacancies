# запросы, пауза, сохранение сырого

import requests
from pathlib import Path
import re
import time
import os

def fetch_page(url: str, headers: dict, file_path: Path) -> Path:
    """
    return html code and save it to /data/raw
    file_path because:
    Проще так: функция как курьер. Ей говорят: «забери посылку по этому адресу и положи вот сюда». Она не решает сама, как назвать посылку и куда её класть. Ей это говорит тот, кто её послал.
    Пример. Цикл по страницам знает, что сейчас страница 5, и говорит функции:
    
    python: fetch_page(url, headers, Path("data/raw/list_p5.html"))

    Функции не нужно гадать по URL, какое имя дать файлу. Ей сказали, она сохранила.
    """
    raw_dir = 'data/raw'

    try:
        page = requests.get(url=url, headers=headers, timeout=10)
        page.raise_for_status()
        time.sleep(1)

        if not os.path.exists(raw_dir):
            Path(raw_dir).mkdir(parents=True, exist_ok=True)


        with open(file_path, "wb") as f:
            f.write(page.content)
        print("Successful page downloading")


    except requests.exceptions.RequestException as e:
        print(f"Error downloading the page: {e}")


def run():
    pass

