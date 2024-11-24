from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Query
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from . import auth
from sqlalchemy import func, asc, desc
import json

router = APIRouter(
    prefix = "/services",
    tags=["Services"]
)

#GET ALL SERVICES
@router.get("/all", response_model=List[schemas.ServiceOut])
def get_all_services(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
    category: Optional[str] = Query(None, description="Filter by category name"),
    city: Optional[str] = Query(None, description="Filter by business city"),
    sort_by: Optional[str] = Query(None, description="Sort by 'price_asc' or 'price_desc'"),
    search: Optional[str] = ""
):
    # Base query
    query = db.query(models.Service)
    
    # Join with Category to filter by category name
    if category:
        query = query.join(models.Category).filter(models.Category.name.ilike(f"%{category}%"))
    
    # Join with Business to filter by city
    if city:
        query = query.join(models.Business).filter(models.Business.city.ilike(f"%{city}%"))
    
    # Filter by search term in service name
    if search:
        query = query.filter(models.Service.name.ilike(f"%{search}%"))
    
    # Sorting by price
    if sort_by == "price_asc":
        query = query.order_by(asc(models.Service.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(models.Service.price))
    
    subscribed_service_ids = db.query(models.Subscription.service_id).filter(models.Subscription.user_id == current_user.user_id).all()
    subscribed_service_ids = [service_id[0] for service_id in subscribed_service_ids]
    
    if subscribed_service_ids:
        query = query.filter(models.Service.service_id.notin_(subscribed_service_ids))
    # Execute query and fetch all results
    services = query.all()

    return services

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
    