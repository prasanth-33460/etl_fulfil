from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String, index=True, nullable=False)
    
    sku = Column(String, unique=True, index=True, nullable=False)
    
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, server_default='true', index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
