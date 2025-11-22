from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, database
from app.routers import upload, products

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

@app.get("/health")
def health_check(db: Session = Depends(database.get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected", "worker": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not reachable: {str(e)}")
