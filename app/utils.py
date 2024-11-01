from passlib.context import CryptContext

#AWS
import boto3
from uuid import uuid4
from .config import settings
from fastapi import UploadFile, HTTPException

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region
)

def upload_image_to_s3(file: UploadFile) -> str:
    try:
        # Generate a unique file name
        file_extension = file.filename.split(".")[-1]
        file_key = f"{uuid4()}.{file_extension}"

        # Upload to S3
        s3_client.upload_fileobj(
            file.file,
            settings.aws_bucket_name,
            file_key,
            ExtraArgs={"ACL": "public-read"}
        )

        # Return the public URL
        return f"https://{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Image upload failed") from e



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


