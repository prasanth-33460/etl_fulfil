import csv
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
ROOT_ENV = ROOT / '.env'
if ROOT_ENV.exists():
    load_dotenv(dotenv_path=ROOT_ENV)

from .database import SessionLocal
from .models import Product

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL is not set in environment. Set REDIS_URL in .env or the environment variables")

celery = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)

celery.conf.broker_transport_options = {'visibility_timeout': 3600}

BATCH_SIZE_ENV = os.getenv("BATCH_SIZE")
if BATCH_SIZE_ENV is None:
    raise RuntimeError("BATCH_SIZE is not set in environment. Set BATCH_SIZE in .env or the environment variables")
try:
    BATCH_SIZE = int(BATCH_SIZE_ENV)
    if BATCH_SIZE <= 0:
        raise ValueError("BATCH_SIZE must be a positive integer")
except (ValueError, TypeError) as e:
    raise RuntimeError(f"Invalid BATCH_SIZE in environment: {e}")

@celery.task(bind=True, name="process_csv_file")
def process_csv_file(self, file_path: str):
    db: Session = SessionLocal()
    total_records = 0
    processed_count = 0
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            total_records = sum(1 for _ in f) - 1
        
        logger.info(f"Task Started. Processing {total_records} records from {file_path}")

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                sku_clean = row.get("sku", "").strip().lower()
                name_clean = row.get("name", "").strip()
                desc_clean = row.get("description", "")

                if not sku_clean or not name_clean:
                    continue

                product_data = {
                    "name": name_clean,
                    "sku": sku_clean,
                    "description": desc_clean,
                    "is_active": True
                }
                batch.append(product_data)
                
                if len(batch) >= BATCH_SIZE:
                    _bulk_upsert(db, batch)
                    processed_count += len(batch)
                    
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': processed_count, 'total': total_records}
                    )
                    batch = []

            if batch:
                _bulk_upsert(db, batch)
                processed_count += len(batch)

            db.commit()
            logger.info(f"Task Completed. Processed {processed_count} records.")

    except Exception as e:
        logger.error(f"Task Failed: {str(e)}", exc_info=True)
        db.rollback()
        return {"status": "Failed", "error": str(e)}
    
    finally:
        db.close()
        if os.path.exists(file_path):
            os.remove(file_path)

    return {"status": "Completed", "total": total_records}


def _bulk_upsert(db: Session, batch_data: list):
    if not batch_data:
        return

    stmt = insert(Product).values(batch_data)
    
    update_stmt = stmt.on_conflict_do_update(
        index_elements=['sku'],
        set_={
            'name': stmt.excluded.name,
            'description': stmt.excluded.description,
        }
    )
    
    db.execute(update_stmt)