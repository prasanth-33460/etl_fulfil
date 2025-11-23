from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(
    prefix="/products",
    tags=["Product Management"]
)

@router.get("/", response_model=list[schemas.ProductResponse])
def list_products(
    skip: int = 0, 
    limit: int = 100, 
    sku: Optional[str] = None,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Product)
    
    if sku:
        query = query.filter(models.Product.sku.ilike(f"%{sku}%"))
    if name:
        query = query.filter(models.Product.name.ilike(f"%{name}%"))
    if is_active is not None:
        query = query.filter(models.Product.is_active == is_active)
        
    return query.offset(skip).limit(limit).all()

@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    db: Session = Depends(database.get_db)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(database.get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@router.delete("/")
def delete_all_products(db: Session = Depends(database.get_db)):
    try:
        num_deleted = db.query(models.Product).delete()
        db.commit()
        return {"message": f"Deleted {num_deleted} products"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
