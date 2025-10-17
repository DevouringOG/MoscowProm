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
from app.db.models import Organization, OrganizationMetrics, OrganizationTaxes, OrganizationAssets, OrganizationProducts, OrganizationMeta
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


@app.get("/organizations", response_class=HTMLResponse)
async def list_organizations(
    request: Request,
    page: int = 1,
    search: str = None,
    db: Session = Depends(get_db)
):
    """
    List all organizations with pagination and search.
    """
    per_page = 20
    offset = (page - 1) * per_page
    
    # Build query
    query = db.query(Organization)
    
    # Apply search filter
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Organization.name.ilike(search_filter)) |
            (Organization.inn.ilike(search_filter))
        )
    
    # Get total count
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    # Get organizations for current page
    organizations = query.order_by(Organization.name).offset(offset).limit(per_page).all()
    
    return templates.TemplateResponse("organizations.html", {
        "request": request,
        "organizations": organizations,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search or "",
    })


@app.get("/organizations/{organization_id}", response_class=HTMLResponse)
async def view_organization(
    request: Request,
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    View detailed information about an organization.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get related data
    metrics = db.query(OrganizationMetrics).filter(
        OrganizationMetrics.organization_id == organization_id
    ).order_by(OrganizationMetrics.year).all()
    
    taxes = db.query(OrganizationTaxes).filter(
        OrganizationTaxes.organization_id == organization_id
    ).order_by(OrganizationTaxes.year).all()
    
    assets = db.query(OrganizationAssets).filter(
        OrganizationAssets.organization_id == organization_id
    ).all()
    
    products = db.query(OrganizationProducts).filter(
        OrganizationProducts.organization_id == organization_id
    ).all()
    
    meta = db.query(OrganizationMeta).filter(
        OrganizationMeta.organization_id == organization_id
    ).first()
    
    return templates.TemplateResponse("organization_detail.html", {
        "request": request,
        "org": org,
        "metrics": metrics,
        "taxes": taxes,
        "assets": assets,
        "products": products,
        "meta": meta,
    })
