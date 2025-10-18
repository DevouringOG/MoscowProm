from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.excel_processor_v2 import process_excel_file
from app.dependencies.templates import templates
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("uploads")

@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are allowed")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = UPLOAD_DIR / f"upload_{timestamp}_{file.filename}"
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info("file_saved", filename=file.filename, path=str(file_path))
        result = process_excel_file(file_path, db)
        logger.info("file_processed", **result)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        error_msg = str(e)
        
        if 'invalid input syntax for type integer' in error_msg:
            user_message = "ОШИБКА: В числовую колонку попало текстовое значение. Проверьте колонки с числовыми данными (отрасль, реестр и др.)"
        elif 'foreign key constraint' in error_msg.lower():
            user_message = "ОШИБКА: Нарушена целостность базы данных"
        elif 'unique constraint' in error_msg.lower() or 'duplicate key' in error_msg.lower():
            user_message = "ОШИБКА: Некоторые ИНН уже существуют в базе"
        elif 'not-null constraint' in error_msg.lower():
            user_message = "ОШИБКА: Отсутствует ИНН или Название у одного или нескольких предприятий"
        elif 'no such file' in error_msg.lower() or 'cannot open' in error_msg.lower():
            user_message = "ОШИБКА: Не удалось открыть Excel файл. Убедитесь, что файл не поврежден"
        else:
            user_message = f"ОШИБКА ОБРАБОТКИ: {error_msg[:200]}"
        
        logger.error("file_processing_failed", error=error_msg, user_message=user_message)
        raise HTTPException(status_code=500, detail=user_message)
    finally:
        try:
            file_path.unlink()
        except Exception as e:
            logger.error("file_cleanup_failed", error=str(e))
