from fastapi import APIRouter, Depends, HTTPException
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
    db: Session = Depends(database.get_db)
):
    return db.query(models.Product).offset(skip).limit(limit).all()


@router.delete("/")
def delete_all_products(db: Session = Depends(database.get_db)):
    try:
        num_deleted = db.query(models.Product).delete()
        db.commit()
        return {"message": f"Deleted {num_deleted} products"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
