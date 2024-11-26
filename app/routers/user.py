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
@router.post("/create", response_model=schemas.UserBase)
def create_user(
    user: schemas.UserCreate = Depends(),
    file: UploadFile = File(None),
    card_number: str = None,
    card_expiry: str = None,
    card_cvc: str = None,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists."
        )

    # Validate required fields
    missing_fields = []
    if not user.email:
        missing_fields.append("email")
    if not user.name:
        missing_fields.append("name")
    if not user.password:
        missing_fields.append("password")
    
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Incorrect Data: Missing {', '.join(missing_fields)}"
        )

    # Validate email format
    if "@" not in user.email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect Data: Invalid email format"
        )

    # Validate profile image
    if file and file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect Data: Wrong type of image. Only jpg and png are allowed."
        )
        
    if not card_number or not card_expiry or not card_cvc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter Valid Card Details"
        )

    # Hash the password
    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    # Upload profile image to S3 if provided
    profile_image = utils.upload_image_to_s3(file) if file else None

    # Create a new user record
    new_user = models.User(**user.dict(), profile_image=profile_image)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If card information is provided, validate and create the card
    if card_number and card_expiry:
        utils.validate_card_format(card_number)
        
        # Determine card brand
        card_brand = utils.get_card_brand(card_number)

        # Create a new card record for the user
        new_card = models.Card(
            user_id=new_user.user_id,
            card_number=card_number,
            card_expiry=card_expiry,
            card_brand=card_brand
        )
        db.add(new_card)
        db.commit()

    # Attach card details to the user response (optional)
    card = db.query(models.Card).filter(models.Card.user_id == new_user.user_id).first()
    if card:
        new_user.card = schemas.CardOut(
            card_number=card.card_number,
            card_expiry=card.card_expiry,
            card_brand=card.card_brand
        )

    return new_user


#GET CURRENT USER
@router.get("/current", response_model=schemas.UserOut)
def get_current_user(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    user = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {current_user.user_id} does not exist")
    card = db.query(models.Card).filter(models.Card.user_id == current_user.user_id).first()
    
    number_of_subscriptions = db.query(models.Subscription).filter(models.Subscription.user_id == current_user.user_id).count()

    # If a card exists, add it to the user response
    card_out = None
    if card:
        card_out = schemas.CardOut(
            card_number=card.card_number,
            card_expiry=card.card_expiry,
            card_brand=card.card_brand
        )
        
        
    user_out = schemas.UserOut(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        profile_image=user.profile_image,
        birthdate=user.birthdate,
        card=card_out,
        number_of_subscriptions=number_of_subscriptions  # Include the subscription count
    )
    
    return user_out

@router.patch("/update", response_model=schemas.UserBase)
def update_user(
    name: str = None,  # Optional fields to update
    email: str = None,
    birthdate: str = None,
    card_number: str = None,
    card_expiry: str = None,
    card_cvc: str = None,
    file: UploadFile = File(None),  # Optional profile image
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

    # Update profile image if a new file is uploaded
    if file:
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Incorrect Data: Wrong type of image. Only jpg and png are allowed."
            )
        # Upload the new image to S3 and get the URL
        profile_image_url = utils.upload_image_to_s3(file)
        user.profile_image = profile_image_url

    # Commit changes to the user record
    db.commit()

    # If card information is provided, update the card    
    if card_number and card_expiry and card_cvc:
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

