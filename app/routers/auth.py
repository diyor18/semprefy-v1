from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models, utils, oauth2


router = APIRouter(
    prefix = "/login",
    tags=["Authentification"]
)

#LOGIN A USER
@router.post("/user", response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends() , db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first() # because OAuth2PasswordRequestForm stores in dict {"username": "smth", "password": "smth"}
    
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    
    access_token = oauth2.create_access_token(data = {"id": user.user_id, "role": "user"})
    return {"access_token" : access_token, "token_type" : "bearer"}

#LOGIN A BUSINESS
@router.post("/business", response_model=schemas.Token)
def login_business(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    
    business = db.query(models.Business).filter(models.Business.email == user_credentials.username).first()
    
    if not business:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    if not utils.verify(user_credentials.password, business.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    
    access_token = oauth2.create_access_token(data={"id": business.business_id, "role": "business"})
    return {"access_token" : access_token, "token_type" : "bearer"}