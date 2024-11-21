from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..config import settings

router = APIRouter(
    prefix = "/businesses",
    tags=["Businesses"]
)

#CREATE A BUSINESS
@router.post("/create", response_model=schemas.BusinessOut)
def create_business(business: schemas.BusinessCreate = Depends(), file: UploadFile = File(None), db: Session = Depends(get_db)):
    #HASHING THE PASSWORD
    hashed_password = utils.hash(business.password)
    business.password = hashed_password
    
    # Upload the image to S3 and get the URL
    profile_image = utils.upload_image_to_s3(file) if file else None
    
    new_business = models.Business(**business.dict(), profile_image = profile_image)
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    
    return new_business

#GET CURRENT BUSINESS
@router.get("/current", response_model=schemas.BusinessOut)
def get_current_business(db: Session = Depends(get_db), current_business: int = Depends(oauth2.get_current_business)):
    business = db.query(models.Business).filter(models.Business.business_id == current_business.business_id).first()
    
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Business with id: {current_business.business_id} does not exist")
    
    return business

#GET BUSINESS BY ID
@router.get("/id/{id}", response_model=schemas.BusinessOut)
def get_business(id: int, db: Session = Depends(get_db)):
    business = db.query(models.Business).filter(models.Business.business_id == id).first()
    
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Business with id: {id} does not exist")
    
    return business