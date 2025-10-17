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


@app.get("/organizations/{organization_id}/edit", response_class=HTMLResponse)
async def edit_organization_page(
    request: Request,
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Show edit form for an organization.
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
    
    return templates.TemplateResponse("organization_edit.html", {
        "request": request,
        "org": org,
        "metrics": metrics,
        "taxes": taxes,
        "assets": assets,
        "products": products,
        "meta": meta,
    })


@app.post("/organizations/{organization_id}/edit")
async def update_organization(
    request: Request,
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Update organization data.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        # Get form data
        form_data = await request.form()
        
        # Update organization basic info
        org.name = form_data.get("name", org.name)
        org.full_name = form_data.get("full_name", org.full_name)
        org.inn = form_data.get("inn", org.inn)
        org.status_spark = form_data.get("status_spark", org.status_spark)
        org.status_internal = form_data.get("status_internal", org.status_internal)
        org.status_final = form_data.get("status_final", org.status_final)
        org.legal_address = form_data.get("legal_address", org.legal_address)
        org.production_address = form_data.get("production_address", org.production_address)
        org.additional_address = form_data.get("additional_address", org.additional_address)
        org.legal_address_coords = form_data.get("legal_address_coords", org.legal_address_coords)
        org.production_address_coords = form_data.get("production_address_coords", org.production_address_coords)
        org.additional_address_coords = form_data.get("additional_address_coords", org.additional_address_coords)
        org.main_industry = form_data.get("main_industry", org.main_industry)
        org.main_subindustry = form_data.get("main_subindustry", org.main_subindustry)
        org.extra_industry = form_data.get("extra_industry", org.extra_industry)
        org.extra_subindustry = form_data.get("extra_subindustry", org.extra_subindustry)
        org.main_okved = form_data.get("main_okved", org.main_okved)
        org.main_okved_name = form_data.get("main_okved_name", org.main_okved_name)
        org.prod_okved = form_data.get("prod_okved", org.prod_okved)
        org.prod_okved_name = form_data.get("prod_okved_name", org.prod_okved_name)
        org.company_info = form_data.get("company_info", org.company_info)
        org.company_size = form_data.get("company_size", org.company_size)
        org.company_size_2022 = form_data.get("company_size_2022", org.company_size_2022)
        org.size_by_employees = form_data.get("size_by_employees", org.size_by_employees)
        org.size_by_employees_2022 = form_data.get("size_by_employees_2022", org.size_by_employees_2022)
        org.size_by_revenue = form_data.get("size_by_revenue", org.size_by_revenue)
        org.size_by_revenue_2022 = form_data.get("size_by_revenue_2022", org.size_by_revenue_2022)
        org.district = form_data.get("district", org.district)
        org.region = form_data.get("region", org.region)
        org.head_name = form_data.get("head_name", org.head_name)
        org.parent_org_name = form_data.get("parent_org_name", org.parent_org_name)
        org.parent_org_inn = form_data.get("parent_org_inn", org.parent_org_inn)
        org.parent_relation_type = form_data.get("parent_relation_type", org.parent_relation_type)
        org.head_contacts = form_data.get("head_contacts", org.head_contacts)
        org.head_email = form_data.get("head_email", org.head_email)
        org.employee_contact = form_data.get("employee_contact", org.employee_contact)
        org.phone = form_data.get("phone", org.phone)
        org.emergency_contact = form_data.get("emergency_contact", org.emergency_contact)
        org.website = form_data.get("website", org.website)
        org.email = form_data.get("email", org.email)
        
        # Update boolean fields
        org.got_moscow_support = form_data.get("got_moscow_support") == "on"
        org.is_system_critical = form_data.get("is_system_critical") == "on"
        
        db.commit()
        logger.info("organization_updated", organization_id=organization_id)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Организация успешно обновлена",
            "organization_id": organization_id
        })
        
    except Exception as e:
        db.rollback()
        logger.error("organization_update_failed", organization_id=organization_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/organizations/{organization_id}")
async def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an organization and all related data.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        db.delete(org)
        db.commit()
        logger.info("organization_deleted", organization_id=organization_id)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Организация успешно удалена"
        })
        
    except Exception as e:
        db.rollback()
        logger.error("organization_delete_failed", organization_id=organization_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
