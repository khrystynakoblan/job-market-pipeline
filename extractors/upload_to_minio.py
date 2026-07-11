import os
import logging
from datetime import date

import boto3
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


def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def upload_jobs_json(local_filepath: str, dt: str = None) -> str:
    if dt is None:
        dt = date.today().isoformat()

    object_key = f"raw/jobs/dt={dt}/data.json"

    client = get_minio_client()

    with open(local_filepath, "rb") as f:
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=f,
            ContentType="application/json",
        )

    logger.info(f"Завантажено {local_filepath} -> s3://{BUCKET_NAME}/{object_key}")
    return object_key


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        logger.error("Використання: python3 upload_to_minio.py <шлях_до_json>")
        exit(1)

    filepath = sys.argv[1]
    upload_jobs_json(filepath)