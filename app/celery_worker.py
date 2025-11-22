import csv
import os
import logging
from celery import Celery
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .config import get_config
from .database import SessionLocal
from .models import Product

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

config = get_config()

celery = Celery(__name__, broker=config.redis_url, backend=config.redis_url)

celery.conf.broker_transport_options = {'visibility_timeout': 3600}

@celery.task(bind=True, name="process_csv_file")
def process_csv_file(self, file_path: str):
    db: Session = SessionLocal()
    processed_count = 0
    task_success = False
    
    try:
        logger.info(f"Task Started. Processing file: {file_path}")

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
                
                if len(batch) >= config.batch_size:
                    _bulk_upsert(db, batch)
                    processed_count += len(batch)
                    
                    self.update_state(
                        state='PROGRESS',
                        meta={'current': processed_count, 'status': 'Processing'}
                    )
                    batch = []

            if batch:
                _bulk_upsert(db, batch)
                processed_count += len(batch)

            db.commit()
            task_success = True
            logger.info(f"Task Completed. Processed {processed_count} records.")

    except Exception as e:
        logger.error(f"Task Failed: {str(e)}", exc_info=True)
        db.rollback()
        return {"status": "Failed", "error": str(e)}
    
    finally:
        db.close()
        
        if os.path.exists(file_path):
            should_delete = False
            
            if config.csv_deletion_policy == "always":
                should_delete = True
                logger.info(f"Deleting CSV file (policy: always): {file_path}")
            elif config.csv_deletion_policy == "success" and task_success:
                should_delete = True
                logger.info(f"Deleting CSV file (policy: success, task succeeded): {file_path}")
            elif config.csv_deletion_policy == "never":
                logger.info(f"Keeping CSV file (policy: never): {file_path}")
            else:
                logger.info(f"Keeping CSV file (policy: {config.csv_deletion_policy}, task_success: {task_success}): {file_path}")
            
            if should_delete:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete CSV file {file_path}: {e}")

    return {"status": "Completed", "total": processed_count}


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