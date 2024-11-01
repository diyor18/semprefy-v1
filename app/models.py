from .database import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.ext.declarative import declarative_base

#example models
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    profile_image = Column(String, nullable=True)
    
    subscriptions = relationship("Subscription", back_populates="user")
    
class Business(Base):
    __tablename__ = "businesses"
    
    business_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    phone = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    profile_image = Column(String, nullable=True)
    
    services = relationship("Service", back_populates="business")
    

class Service(Base):
    __tablename__ = "services"
    
    service_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    tier = Column(Integer, nullable=True)
    price = Column(Integer, nullable=False)
    billing_cycle = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    service_image = Column(String, nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.business_id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    
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
    subscription_id = Column(Integer, ForeignKey("subscriptions.subscription_id", ondelete="CASCADE"), nullable=False)
    
    subscription = relationship("Subscription", back_populates="transactions")
    
class Vote(Base):
    __tablename__ = "votes"
    
    user_id = Column(Integer, ForeignKey("users.user_id" ,ondelete="CASCADE"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.service_id", ondelete="CASCADE"), primary_key=True)