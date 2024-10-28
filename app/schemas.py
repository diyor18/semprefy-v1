from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from typing_extensions import Annotated

class UserBase(BaseModel):
    email: EmailStr
    name: str
    
class UserCreate(UserBase):
    password: str
    
class UserOut(UserBase):
    user_id: int
    created_at: datetime
        
    class Config:
        from_attributes = True
        
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
    
class Subscription(BaseModel):
    user_id: int
    service_id: int
    user: UserOut
    service: ServiceOut
    
    class Config:
        from_attributes = True
    