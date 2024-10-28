from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from . import auth
#NOT A NECESSARY ROUTER
router = APIRouter(
    prefix = "/vote",
    tags=["Votes"]
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(vote: schemas.Vote, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    
    service = db.query(models.Service).filter(models.Service.service_id == vote.service_id).first() 
    
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Service with id {vote.service_id} doesn't exist")
    
    vote_query = db.query(models.Vote).filter(models.Vote.service_id == vote.service_id, models.Vote.user_id == current_user.user_id)
    found_vote = vote_query.first()
    if(vote.dir == 1):
        if found_vote:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"user {current_user.name} has already voted on post")
        new_vote = models.Vote(service_id = vote.service_id, user_id = current_user.user_id)
        db.add(new_vote)
        db.commit()
        return{"message":"successfully added vote"}
    else:
        if not found_vote:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vote does not exist")
        
        vote_query.delete(synchronize_session=False)
        db.commit()
        
        return {"message" : "successfully deleted vote"}