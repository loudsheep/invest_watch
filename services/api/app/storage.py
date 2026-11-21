"""Evidence storage client - talks to Garage (S3-compatible), not MinIO.
The `minio` python package is just an S3 client despite the name; it works
against any S3-compatible endpoint, Garage included.
"""
from functools import lru_cache

from investwatch_common.config import settings
from minio import Minio


@lru_cache
def get_client() -> Minio:
    endpoint = settings.s3_endpoint.replace("http://", "").replace("https://", "")
    return Minio(
        endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_endpoint.startswith("https"),
        region=settings.s3_region,
    )


def get_object(key: str) -> bytes:
    response = get_client().get_object(settings.s3_bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
