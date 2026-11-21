"""Evidence storage client - talks to Garage (S3-compatible), not MinIO.
The `minio` python package is just an S3 client despite the name; it works
against any S3-compatible endpoint, Garage included. The bucket itself is
normally created once by garage/init.sh; make_bucket here is just a safety
net for a fresh Garage node that hasn't been initialized yet.
"""
import io
from functools import lru_cache

from investwatch_common.config import settings
from minio import Minio


@lru_cache
def get_client() -> Minio:
    endpoint = settings.s3_endpoint.replace("http://", "").replace("https://", "")
    client = Minio(
        endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_endpoint.startswith("https"),
    )
    if not client.bucket_exists(settings.s3_bucket):
        client.make_bucket(settings.s3_bucket)
    return client


def put_object(key: str, data: bytes, content_type: str) -> None:
    client = get_client()
    client.put_object(settings.s3_bucket, key, io.BytesIO(data), length=len(data), content_type=content_type)
