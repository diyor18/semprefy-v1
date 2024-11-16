from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..config import settings
from datetime import datetime

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
    profile_image = utils.upload_image_to_s3(file) if file else None
    
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
    card = db.query(models.Card).filter(models.Card.user_id == current_user.user_id).first()
    
    # If a card exists, add it to the user response
    if card:
        user.card = schemas.CardOut(
            card_number=card.card_number,
            card_expiry=card.card_expiry,
            card_brand=card.card_brand
        )
    return user

@router.patch("/update", response_model=schemas.UserOut)
def update_user(
    name: str = None,  # Optional fields to update
    email: str = None,
    birthdate: str = None,
    card_number: str = None,
    card_expiry: str = None,
    db: Session = Depends(get_db),  # Database session
    current_user: int = Depends(oauth2.get_current_user)  # Current logged-in user
):
    # Fetch the current user from the database
    user = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {current_user.user_id} does not exist")

    # Update user fields if provided
    if name:
        user.name = name
    if email:
        user.email = email
    if birthdate:
        try:
            user.birthdate = datetime.strptime(birthdate, "%d/%m/%Y").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid birthdate format. Use dd/mm/yyyy."
            )

    # Commit changes to the user record
    db.commit()

    # If card information is provided, update the card
    if card_number and card_expiry:
        
        utils.validate_card_format(card_number)
        
        # Determine card brand
        card_brand = utils.get_card_brand(card_number)

        # Check if a card already exists for the user
        card = db.query(models.Card).filter(models.Card.user_id == current_user.user_id).first()
        
        if card:
            # Update the existing card
            card.card_number = card_number
            card.card_expiry = card_expiry
            card.card_brand = card_brand
        else:
            # If no card exists, create a new card
            new_card = models.Card(
                user_id=current_user.user_id,
                card_number=card_number,
                card_expiry=card_expiry,
                card_brand=card_brand
            )
            db.add(new_card)
        
        db.commit()

    # Refresh and return the updated user
    db.refresh(user)
    card = db.query(models.Card).filter(models.Card.user_id == current_user.user_id).first()
    
    # If a card exists, add it to the user response
    if card:
        user.card = schemas.CardOut(
            card_number=card.card_number,
            card_expiry=card.card_expiry,
            card_brand=card.card_brand
        )
    return user

