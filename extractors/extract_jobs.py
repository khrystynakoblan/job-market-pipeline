import os
import logging
import json
from datetime import date

import requests
from dotenv import load_dotenv

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search"



class RateLimitError(Exception):
    pass


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((requests.exceptions.RequestException, RateLimitError)),
    reraise=True,
)
def fetch_page(page: int, query: str = "data engineer") -> dict:
    url = f"{BASE_URL}/{page}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 50,
        "what": query,
        "content-type": "application/json",
    }

    logger.info(f"Запит сторінки {page} (query='{query}')")
    response = requests.get(url, params=params, timeout=15)

    if response.status_code == 429:
        logger.warning("Отримано 429 rate-limit, повторюємо з backoff")
        raise RateLimitError("Rate limit exceeded")

    response.raise_for_status()
    return response.json()

MAX_PAGES = 5


def extract_all_jobs(query: str = "data engineer") -> list[dict]:
    all_jobs = []

    for page in range(1, MAX_PAGES + 1):
        try:
            data = fetch_page(page, query=query)
        except Exception as e:
            logger.error(f"Не вдалося отримати сторінку {page} після всіх спроб: {e}")
            break

        results = data.get("results", [])
        if not results:
            logger.info(f"Сторінка {page} порожня, зупиняємось")
            break

        all_jobs.extend(results)
        logger.info(f"Отримано {len(results)} вакансій зі сторінки {page}")

    logger.info(f"Всього зібрано {len(all_jobs)} вакансій")
    return all_jobs

def save_locally(jobs: list[dict], filepath: str = None) -> str:
    if filepath is None:
        today = date.today().isoformat()
        filepath = f"data_{today}.json"

    payload = {
        "extracted_at": date.today().isoformat(),
        "count": len(jobs),
        "jobs": jobs,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(f"Збережено {len(jobs)} вакансій у {filepath}")
    return filepath

if __name__ == "__main__":
    from upload_to_minio import upload_jobs_json
    from load_to_raw import fetch_json_from_minio, load_to_raw

    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.error("ADZUNA_APP_ID / ADZUNA_APP_KEY не знайдені в .env")
        exit(1)

    jobs = extract_all_jobs(query="data engineer")
    local_path = save_locally(jobs)
    object_key = upload_jobs_json(local_path)

    data = fetch_json_from_minio(object_key)
    load_to_raw(data, source_file=object_key)