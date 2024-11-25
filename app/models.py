from .database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date, CheckConstraint, Float
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

#example models
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    profile_image = Column(String, nullable=True)
    birthdate = Column(Date, nullable=True)
    
    subscriptions = relationship("Subscription", back_populates="user")
    cards = relationship("Card", back_populates="user")
    

class Card(Base):
    __tablename__ = "cards"
    
    card_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    card_number = Column(String(19), nullable=False)
    card_expiry = Column(String(5), nullable=False)
    card_brand = Column(String, nullable=False)
    
    user = relationship("User", back_populates="cards")
    
    
class Business(Base):
    __tablename__ = "businesses"
    
    business_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    profile_image = Column(String, nullable=False)
    country = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)
    bank_account = Column(String, nullable=False)
    bank_account_name = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    
    services = relationship("Service", back_populates="business")    

class Service(Base):
    __tablename__ = "services"
    
    service_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    business_id = Column(Integer, ForeignKey("businesses.business_id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    duration = Column(Integer, nullable=False, default=12)  # duration in months
    status = Column(String, nullable=False, default="active")
    
    category = relationship("Category", back_populates="services")
    business = relationship("Business", back_populates="services")
    subscription = relationship("Subscription", back_populates="service")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    expiry_date = Column(Date, nullable=True)
    status = Column(String, nullable=True)
    total_days_left = Column(Integer, nullable=True)
    days_till_next_payment = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id" ,ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.service_id", ondelete="CASCADE"), nullable=False)
    
    
    service = relationship("Service", back_populates="subscription")
    user = relationship("User", back_populates="subscriptions")
    transactions = relationship("Transaction", back_populates="subscription")
    
    @hybrid_property
    def progress_bar_next_payment(self):
        if self.days_till_next_payment is not None:
            progress = (30 - self.days_till_next_payment) / 30
            return round(progress, 1)  # Round to 1 decimal
        return None

class Category(Base):
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=True)
    name = Column(String, nullable=False)
    category_image = Column(String, nullable=True)
    ranking = Column(Integer, nullable=True)
    
    services = relationship("Service", back_populates="category")
    
class Transaction(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    status = Column(String, nullable=False)
    card_brand = Column(String, nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.subscription_id", ondelete="CASCADE"), nullable=False)
    
    subscription = relationship("Subscription", back_populates="transactions")
    