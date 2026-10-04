import boto3
from botocore.config import Config
from backend.config import settings
from typing import Optional, BinaryIO, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# S3 client
s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    endpoint_url=settings.MLFLOW_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
)

def _parse_s3_uri(uri_or_key: str, default_bucket: str = None):
    """Extract bucket and key from an S3 URI (s3://bucket/key) or return default_bucket and key."""
    if not uri_or_key:
        return default_bucket or settings.S3_BUCKET_NAME, ""
    if uri_or_key.startswith("s3://"):
        parts = uri_or_key[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        return bucket, key
    return default_bucket or settings.S3_BUCKET_NAME, uri_or_key

import os
import shutil

LOCAL_STORAGE_DIR = os.path.join(os.getcwd(), "local_storage")

def upload_to_s3(data: Any, key: str, bucket: str = None) -> str:
    """Upload bytes, str, or buffer to S3 or local storage and return the S3 URI"""
    bucket, key = _parse_s3_uri(key, bucket)
    if hasattr(data, "getvalue"):
        data = data.getvalue()
    elif isinstance(data, str):
        data = data.encode("utf-8")
    
    if settings.AWS_ACCESS_KEY_ID:
        try:
            s3_client.put_object(Bucket=bucket, Key=key, Body=data)
            return f"s3://{bucket}/{key}"
        except Exception as e:
            logger.debug(f"S3 put_object failed ({e}), falling back to local file storage")
    
    # Local fallback
    local_path = os.path.join(LOCAL_STORAGE_DIR, bucket, key)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(data)
    return f"s3://{bucket}/{key}"

def download_from_s3(key: str, bucket: str = None) -> bytes:
    """Download bytes from S3 or local storage"""
    bucket, key = _parse_s3_uri(key, bucket)
    if settings.AWS_ACCESS_KEY_ID:
        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.debug(f"S3 get_object failed ({e}), falling back to local file storage")
    
    local_path = os.path.join(LOCAL_STORAGE_DIR, bucket, key)
    if os.path.exists(local_path):
        with open(local_path, "rb") as f:
            return f.read()
    raise FileNotFoundError(f"Artifact not found in S3 or local storage: {bucket}/{key}")

def upload_file_to_s3(file_path: str, key: str, bucket: str = None) -> str:
    """Upload a file to S3 or local storage"""
    bucket, key = _parse_s3_uri(key, bucket)
    if settings.AWS_ACCESS_KEY_ID:
        try:
            s3_client.upload_file(file_path, bucket, key)
            return f"s3://{bucket}/{key}"
        except Exception as e:
            logger.debug(f"S3 upload_file failed ({e}), falling back to local file storage")
    
    local_path = os.path.join(LOCAL_STORAGE_DIR, bucket, key)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    shutil.copyfile(file_path, local_path)
    return f"s3://{bucket}/{key}"

def get_presigned_url(key: str, bucket: str = None, expiration: int = 900) -> str:
    """Generate a presigned URL for downloading or a local endpoint URL"""
    bucket, key = _parse_s3_uri(key, bucket)
    if settings.AWS_ACCESS_KEY_ID:
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expiration,
            )
            return url
        except Exception:
            pass
    return f"/api/v1/jobs/artifacts/{bucket}/{key}"

def delete_from_s3(key: str, bucket: str = None) -> bool:
    """Delete an object from S3"""
    bucket, key = _parse_s3_uri(key, bucket)
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        logger.error(f"Failed to delete {key} from S3: {e}")
        return False

def list_s3_objects(prefix: str, bucket: str = None) -> list:
    """List objects in S3 with given prefix"""
    bucket, prefix = _parse_s3_uri(prefix, bucket)
    paginator = s3_client.get_paginator("list_objects_v2")
    objects = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if "Contents" in page:
            objects.extend([obj["Key"] for obj in page["Contents"]])
    return objects