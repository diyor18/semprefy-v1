from passlib.context import CryptContext

#AWS
import boto3
from uuid import uuid4
from .config import settings
from fastapi import UploadFile, HTTPException, status
import logging
import re

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region
)

def upload_image_to_s3(file: UploadFile) -> str:
    if not file:
        # No file provided, so return None or a default URL if you have one
        return None
    try:
        # Generate a unique file name
        file_extension = file.filename.split(".")[-1]
        if not file_extension:
            raise ValueError("The file must have an extension.")
        
        file_key = f"{uuid4()}.{file_extension}"
        
          # Log debug information
        logger.info(f"Attempting to upload file with key: {file_key}")
        logger.info(f"Uploading to bucket: {settings.aws_bucket_name}, region: {settings.aws_region}")

        # Upload to S3
        s3_client.upload_fileobj(
            file.file,
            settings.aws_bucket_name,
            file_key
        )

        # Return the public URL
        
        # Construct and return the public URL
        file_url = f"https://{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"
        logger.info(f"File uploaded successfully. URL: {file_url}")
        
        return file_url
    
    except s3_client.exceptions.NoSuchBucket:
        logger.error("Bucket does not exist. Check AWS_BUCKET_NAME in .env")
        raise HTTPException(status_code=500, detail="Image upload failed: Bucket does not exist.")
    
    except s3_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"AWS ClientError occurred: {error_code}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {error_code}")
    
    except Exception as e:
        logger.error(f"Unexpected error uploading file to S3: {e}")  # Detailed error log
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)




def get_card_brand(card_number: str) -> str:
    # Remove spaces to validate the actual digits
    clean_number = card_number.replace(" ", "")
    # Visa cards start with a 4
    if re.match(r"^4\d{15}$", clean_number):  # Visa cards must have exactly 16 digits
        return "Visa"
    # MasterCard cards start with 51-55 or 2221-2720
    elif re.match(r"^5[1-5]\d{14}$", clean_number) or re.match(r"^2(2[2-9]\d{2}|[3-6]\d{3}|7[0-1]\d{2}|720)\d{12}$", clean_number):
        return "Mastercard"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid card number. Only Visa and MasterCard are accepted."
        )
        
        
def validate_card_format(card_number: str):
    if not re.match(r"^\d{4} \d{4} \d{4} \d{4}$", card_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Card number must be in the format 'xxxx xxxx xxxx xxxx'."
        )