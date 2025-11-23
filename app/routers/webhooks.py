from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, database
import requests

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)

@router.post("/", response_model=schemas.WebhookResponse)
def create_webhook(webhook: schemas.WebhookCreate, db: Session = Depends(database.get_db)):
    db_webhook = models.Webhook(**webhook.model_dump())
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    return db_webhook

@router.get("/", response_model=list[schemas.WebhookResponse])
def list_webhooks(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return db.query(models.Webhook).offset(skip).limit(limit).all()

@router.put("/{webhook_id}", response_model=schemas.WebhookResponse)
def update_webhook(webhook_id: int, webhook_update: schemas.WebhookUpdate, db: Session = Depends(database.get_db)):
    webhook = db.query(models.Webhook).filter(models.Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    update_data = webhook_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(webhook, key, value)
    
    db.commit()
    db.refresh(webhook)
    return webhook

@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: int, db: Session = Depends(database.get_db)):
    webhook = db.query(models.Webhook).filter(models.Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(webhook)
    db.commit()
    return {"message": "Webhook deleted"}

@router.post("/{webhook_id}/test")
def test_webhook(webhook_id: int, db: Session = Depends(database.get_db)):
    webhook = db.query(models.Webhook).filter(models.Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    try:
        response = requests.post(
            webhook.url, 
            json={"event": "test_ping", "message": "This is a test webhook from Product Importer"},
            timeout=5
        )
        return {
            "status": "success", 
            "status_code": response.status_code,
            "response_time_ms": response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
