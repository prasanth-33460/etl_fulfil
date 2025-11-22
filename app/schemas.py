from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Product Name")
    sku: str = Field(..., min_length=1, max_length=100, description="Unique Stock Keeping Unit")
    description: Optional[str] = Field(None, description="Detailed product description")
    is_active: bool = Field(default=True, description="Is the product available for sale?")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)