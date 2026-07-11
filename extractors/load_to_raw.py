import os
import json
import logging

import boto3
import psycopg2
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
BUCKET_NAME = "raw-data"

POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")


def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def get_postgres_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
    )


def fetch_json_from_minio(object_key: str) -> dict:
    client = get_minio_client()
    response = client.get_object(Bucket=BUCKET_NAME, Key=object_key)
    raw_bytes = response["Body"].read()
    data = json.loads(raw_bytes)
    logger.info(f"Прочитано {object_key} з MinIO, {data.get('count', 0)} вакансій")
    return data


def load_to_raw(data: dict, source_file: str):
    jobs = data.get("jobs", [])

    conn = get_postgres_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM raw.jobs_raw WHERE source_file = %s", (source_file,))
    deleted = cur.rowcount
    if deleted:
        logger.info(f"Видалено {deleted} старих рядків для {source_file} (idempotency)")

    for job in jobs:
        cur.execute(
            "INSERT INTO raw.jobs_raw (payload, source_file) VALUES (%s, %s)",
            (json.dumps(job), source_file),
        )

    conn.commit()
    cur.close()
    conn.close()

    logger.info(f"Завантажено {len(jobs)} вакансій у raw.jobs_raw (source_file={source_file})")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        logger.error("Використання: python3 load_to_raw.py <object_key_в_minio>")
        logger.error("Приклад: python3 load_to_raw.py raw/jobs/dt=2026-07-11/data.json")
        exit(1)

    object_key = sys.argv[1]
    data = fetch_json_from_minio(object_key)
    load_to_raw(data, source_file=object_key)