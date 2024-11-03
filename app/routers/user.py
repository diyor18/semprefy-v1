from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..config import settings

router = APIRouter(
    prefix = "/users",
    tags=["Users"]
)

#CREATE A USER
@router.post("/create", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate = Depends(), file: UploadFile = File(None), db: Session = Depends(get_db)):
    #HASHING THE PASSWORD
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    
    # Upload the image to S3 and get the URL
    profile_image = utils.upload_image_to_s3(file)
    
    # Create a new user record with image URL
    new_user = models.User(**user.dict(), profile_image = profile_image)
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
