import boto3
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

#Boto Start
S3_BUCKET_NAME = "semprefyv1"

s3 = boto3.client("s3")

#Boto End
router = APIRouter(
    prefix = "/users",
    tags=["Users"]
)

#CREATE A USER
@router.post("/create", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    #HASHING THE PASSWORD
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

#GET CURRENT USER
@router.get("/current", response_model=schemas.UserOut)
def get_current_user(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {current_user.user_id} does not exist")
    
    return user

# @router.get("/{id}", response_model=schemas.UserOut)
# def get_user(id: int, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.user_id == id).first()
    
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} does not exist")
    
#     return user



#dummy photo uploader

@router.post("/photos", status_code=201)
def upload_photo(file: UploadFile):
    print(file.filename)
    print(file.content_type)
    
    #upload to aws
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(S3_BUCKET_NAME)
    bucket.upload_fileobj(file.file, file.filename)