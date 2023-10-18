import os
from datetime import timedelta

from google.cloud import storage


def upload_to_storage(source_file_path: str) -> str:
    storage_client = storage.Client()
    bucket_name = os.environ["BUCKET_NAME"]
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_path)
    blob.upload_from_filename(source_file_path)
    signed_url = blob.generate_signed_url(
        version="v2",
        expiration=timedelta(days=365),
        method="GET",
    )
    return signed_url
