from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional
from typing_extensions import Annotated


class CardOut(BaseModel):
    card_number: str
    card_expiry: str
    card_brand: str

    class Config:
        from_attributes = True   
        
class UserBase(BaseModel):
    email: EmailStr
    name: str
    
class UserCreate(UserBase):
    password: str
    
class UserOut(UserBase):
    user_id: int
    created_at: datetime
    number_of_subscriptions: int  # New field added
    profile_image: Optional[str] = None
    birthdate: Optional[datetime] = None
    card: Optional[CardOut] = None  

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
        
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    id: Optional[int] = None
    role: Optional[str] = None
    
class BusinessBase(BaseModel):
    email: EmailStr
    name: str
    
class BusinessCreate(UserBase):
    password: str
    phone: int
    
class BusinessOut(UserBase):
    business_id: int
    created_at: datetime
    phone: int
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True
    
class ServiceBase(BaseModel):
    name:str
    description:str
    price:int
    billing_cycle: str
    
class ServiceCreate(ServiceBase):
    pass

class ServiceOut(ServiceBase):
    service_id: int
    business_id: int
    business: BusinessOut
    
    class Config:
        from_attributes = True
        
        
class Vote(BaseModel):
    service_id: int
    dir: Annotated[int, Field(strict=True, ge=0, le=1)]
    
class ServiceVote(ServiceBase):
    Service: ServiceOut
    votes: int
    
    class Config:
        from_attributes = True
        
class Category(BaseModel):
    name: str
    category_image: str
    description: str
    
    
class Subscription(BaseModel):
    user_id: int
    service_id: int
    days_till_next_payment: int
    subscription_date: datetime
    expiry_date: datetime
    status: str
    user: UserBase
    service: ServiceOut
    
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
        
        
        
class Transaction(BaseModel):
    transaction_id: int
    amount: int
    created_at: datetime
    status: str
    subscription_id: int

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }