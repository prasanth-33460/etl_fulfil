import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from celery.result import AsyncResult
from app.celery_worker import process_csv_file, celery

router = APIRouter(
    prefix="/upload",
    tags=["Upload Operations"]
)

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file format. Only .csv files are supported."
        )

    temp_filename = f"temp_{file.filename}"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if os.path.getsize(temp_filename) == 0:
            os.remove(temp_filename)
            raise HTTPException(status_code=400, detail="File is empty.")
            
    except Exception as e:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

    task = process_csv_file.delay(temp_filename)

    return {
        "message": "File uploaded successfully. Processing started.",
        "task_id": task.id
    }


@router.get("/{task_id}")
def get_upload_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery)

    response = {
        "task_id": task_id,
        "status": task_result.state,
        "progress_percent": 0,
        "details": None
    }

    if task_result.state == 'PROGRESS':
        data = task_result.info
        current = data.get("current", 0)
        total = data.get("total", 1)
        
        if total > 0:
            response["progress_percent"] = round((current / total) * 100, 2)
        
        response["details"] = {
            "processed_rows": data.get("rows_processed", "Calculating..."),
            "bytes_read": current,
            "total_bytes": total
        }
    
    elif task_result.state == 'SUCCESS':
        response["progress_percent"] = 100
        response["status"] = "COMPLETED"
        response["details"] = task_result.result
        
    elif task_result.state == 'FAILURE':
        response["status"] = "FAILED"
        response["error"] = str(task_result.info)

    return response
