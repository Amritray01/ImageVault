import os
import io
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Tuple
from app.config import settings

class StorageService:
    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        self.s3_client = None
        
        if self.backend == "s3" or settings.AWS_ACCESS_KEY_ID:
            session = boto3.session.Session()
            client_kwargs = {}
            if settings.AWS_REGION:
                client_kwargs["region_name"] = settings.AWS_REGION
            if settings.S3_ENDPOINT_URL:
                client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                client_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                client_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            
            # Automatically uses EC2 IAM Instance Profile (ImgVaultEC2Role) when keys are omitted
            self.s3_client = session.client("s3", **client_kwargs)
            # Ensure bucket exists
            try:
                self.s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            except Exception:
                try:
                    if settings.AWS_REGION == "us-east-1":
                        self.s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=settings.S3_BUCKET_NAME,
                            CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION}
                        )
                except Exception as e:
                    print(f"[Storage] Note: S3 bucket initialization notice: {e}")
        else:
            # Ensure local storage folders exist
            os.makedirs(os.path.join(settings.LOCAL_STORAGE_DIR, "images"), exist_ok=True)
            os.makedirs(os.path.join(settings.LOCAL_STORAGE_DIR, "thumbnails"), exist_ok=True)

    async def save_image_and_thumbnail(
        self,
        storage_filename: str,
        jpeg_bytes: bytes,
        thumbnail_bytes: bytes
    ) -> Tuple[str, str]:
        """
        Persists compressed JPEG and thumbnail to S3 or Local storage.
        Returns: (image_path_or_key, thumbnail_path_or_key)
        """
        img_key = f"images/{storage_filename}"
        thumb_key = f"thumbnails/thumb_{storage_filename}"

        if self.s3_client:
            # Upload to S3 / MinIO
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=img_key,
                Body=jpeg_bytes,
                ContentType="image/jpeg",
                Metadata={"compressed": "true", "format": "JPEG"}
            )
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=thumb_key,
                Body=thumbnail_bytes,
                ContentType="image/jpeg"
            )
            return img_key, thumb_key
        else:
            # Save to local storage directory
            img_abs_path = os.path.join(settings.LOCAL_STORAGE_DIR, "images", storage_filename)
            thumb_abs_path = os.path.join(settings.LOCAL_STORAGE_DIR, "thumbnails", f"thumb_{storage_filename}")
            
            with open(img_abs_path, "wb") as f:
                f.write(jpeg_bytes)
            with open(thumb_abs_path, "wb") as f:
                f.write(thumbnail_bytes)
                
            return img_key, thumb_key

    async def get_file_bytes(self, key_or_path: str) -> Optional[bytes]:
        """Retrieve binary content from S3 or local storage."""
        if self.s3_client:
            try:
                response = self.s3_client.get_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=key_or_path
                )
                return response["Body"].read()
            except ClientError:
                return None
        else:
            abs_path = os.path.join(settings.LOCAL_STORAGE_DIR, key_or_path.replace("/", os.sep))
            if os.path.exists(abs_path):
                with open(abs_path, "rb") as f:
                    return f.read()
            return None

    async def delete_file(self, key_or_path: str) -> bool:
        """Delete file from S3 or local filesystem."""
        if self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key_or_path)
                return True
            except ClientError:
                return False
        else:
            abs_path = os.path.join(settings.LOCAL_STORAGE_DIR, key_or_path.replace("/", os.sep))
            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                    return True
                except OSError:
                    return False
            return False

storage_service = StorageService()
