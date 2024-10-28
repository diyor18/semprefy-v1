from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix = "/categories",
    tags=["Categories"]
)

#GET All CATEGORIES
@router.get("/all", response_model=List[schemas.Category])
def categories(db: Session = Depends(get_db)):
    categories = db.query(models.Category).all()
    return categories

#GET TOP CATEGORIES
@router.get("/top", response_model=List[schemas.Category])
def categories(db: Session = Depends(get_db), limit: int = 10):
    categories = db.query(models.Category).limit(limit).all()
    return categories