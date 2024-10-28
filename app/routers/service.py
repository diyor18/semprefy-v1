from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from . import auth
from sqlalchemy import func
import json

router = APIRouter(
    prefix = "/services",
    tags=["Services"]
)

#GET ALL SERVICES
@router.get("/all", response_model=List[schemas.ServiceOut]) #List[schemas.ServiceVote]
def get_all_services(db: Session = Depends(get_db), limit: int = 10, skip: int = 0, search: Optional[str] = ""): #here limit is a query parameter [URL?limit=10]. Use %20 for a space ' '
    services = db.query(models.Service).filter(models.Service.name.contains(search)).limit(limit).offset(skip).all()
    
    #results = db.query(models.Service, func.count(models.Vote.service_id).label("votes")).join(models.Vote, models.Vote.service_id == models.Service.service_id, isouter=True).group_by(models.Service.service_id).all()
    #try later with creating votes column in Service model, later counting it here in the func and assign it as the service.votes. Change the schema as well.
    return services #results

#CREATE A SERVICE
@router.post("/create", response_model=schemas.ServiceOut)
def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_db), current_business: int = Depends(oauth2.get_current_business)):

    new_service = models.Service(business_id = current_business.business_id, **service.dict())
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    
    return new_service

#GET MY SERVICES
@router.get("/my_services", response_model=List[schemas.ServiceOut])
def get_my_services(db: Session = Depends(get_db), current_business: int = Depends(oauth2.get_current_business)):
    print(db.query(models.Service).filter(models.Service.business_id == current_business.business_id).all())
    return db.query(models.Service).filter(models.Service.business_id == current_business.business_id).all()

#GET SERVICE BY ID
@router.get("/{id}", response_model=schemas.ServiceOut)
def get_service(id: int, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.service_id == id).first()
    
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service with id: {id} does not exist")
    
    return service

#DELETE A SERVICE
@router.delete("/delete/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db), current_business: int = Depends(oauth2.get_current_business)):
    service_query = db.query(models.Service).filter(models.Service.service_id == service_id)
    service = service_query.first()
    
    if service == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service with id: {id} does not exist")
    
    if service.business_id != current_business.business_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised to perfom the requested action")
    service_query.delete(synchronize_session=False)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

#UPDATE A SERVICE
@router.put("/update/{service_id}", response_model=schemas.ServiceOut)
def update_post(service_id: int, updated_service: schemas.ServiceCreate, db: Session = Depends(get_db), current_business: int = Depends(oauth2.get_current_business)):
    service_query = db.query(models.Service).filter(models.Service.service_id == service_id)
    
    service = service_query.first()
    if service == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service with id: {id} does not exist")
    print(current_business.name)
    if service.business_id != current_business.business_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised to perfom the requested action")
    
    service_query.update(updated_service.dict(), synchronize_session=False)
    db.commit()
    
    return service
    