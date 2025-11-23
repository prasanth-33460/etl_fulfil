from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from app import models, database
from app.routers import upload, products, webhooks

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="Product Importer API",
    description="High-performance CSV importer with async processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(products.router)
app.include_router(webhooks.router)

static_dir = os.path.join(os.path.dirname(__file__), "app/static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/")
def root():
    return {"message": "Welcome to Product Importer API. Go to /ui for the frontend."}

@app.get("/health")
def health_check(db: Session = Depends(database.get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "worker": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Database not reachable: {str(e)}"
        ) from e
