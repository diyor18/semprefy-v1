from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Optional
from typing_extensions import Annotated


class CategoryOut(BaseModel):
    name: str
    category_image: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

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
    number_of_subscriptions: int
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
    phone: str
    description: str
    country: str
    city: str
    address: str
    bank_account: str
    bank_account_name: str
    bank_name: str
    
class BusinessCreate(BusinessBase):
    password: str
    
class BusinessOut(BusinessBase):
    business_id: int
    created_at: datetime
    profile_image: Optional[str] = None
    
    class Config:
        from_attributes = True
    
class ServiceBase(BaseModel):
    name: str
    description: str
    price: float
    duration: int
    
class ServiceCreate(ServiceBase):
    pass

class ServiceOut(ServiceBase):
    service_id: int
    business_id: int
    business: BusinessOut
    category: Optional[CategoryOut] = None
    status: str
    
    class Config:
        from_attributes = True
        
    
class ServiceVote(ServiceBase):
    Service: ServiceOut
    votes: int
    
    class Config:
        from_attributes = True
        
    
class Subscription(BaseModel):
    user_id: int
    service_id: int
    days_till_next_payment: int
    subscription_date: datetime
    expiry_date: datetime
    status: str
    progress_bar_next_payment: Optional[float]  # Include computed field
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
    card_brand: str
    subscription: Subscription

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.strftime("%d/%m/%Y") if v else None
        }
        
        
class UserSubscriptionOut(BaseModel):
    subscription_id: int
    user_name: str
    email: str
    profile_image: Optional[str]
    service_name: str
    subscription_date: datetime  # Use datetime for timestamps
    expiry_date: Optional[date]  # Use date for dates
    price: float

    class Config:
        from_attributes = True