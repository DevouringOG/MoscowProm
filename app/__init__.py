"""Application package."""
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.logger import setup_logging, get_logger
from app.db import engine, Base, get_db
from app.services.excel_processor import process_excel_file
from config import settings, ensure_directories

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Ensure required directories exist
ensure_directories()

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting", version=settings.app_version)
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_tables_created")
    except Exception as e:
        logger.error("database_tables_creation_failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Web application for analyzing industrial enterprises in Moscow",
    docs_url=None,  # Disable API docs
    redoc_url=None,  # Disable ReDoc
    lifespan=lifespan,
)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process Excel file with organization data.
    """
    # Validate file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are allowed")
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = UPLOAD_DIR / f"upload_{timestamp}_{file.filename}"
    
    try:
        # Save uploaded file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info("file_saved", filename=file.filename, path=str(file_path))
        
        # Process Excel file
        result = process_excel_file(file_path, db)
        
        logger.info("file_processed", **result)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error("file_processing_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up uploaded file
        try:
            file_path.unlink()
        except Exception as e:
            logger.error("file_cleanup_failed", error=str(e))
