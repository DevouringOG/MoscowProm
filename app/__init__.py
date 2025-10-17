"""Application package."""
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends, Query
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
    industry: list[str] = Query(None),
    district: list[str] = Query(None),
    region: list[str] = Query(None),
    size: list[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all organizations with pagination, search and multiple filters.
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
    
    # Apply industry filter (multiple values with OR)
    if industry:
        industry_filters = []
        for ind in industry:
            industry_filters.append(Organization.main_industry.ilike(f"%{ind}%"))
            industry_filters.append(Organization.extra_industry.ilike(f"%{ind}%"))
        from sqlalchemy import or_
        query = query.filter(or_(*industry_filters))
    
    # Apply district filter (multiple values with OR)
    if district:
        district_filters = [Organization.district.ilike(f"%{d}%") for d in district]
        from sqlalchemy import or_
        query = query.filter(or_(*district_filters))
    
    # Apply region filter (multiple values with OR)
    if region:
        region_filters = [Organization.region.ilike(f"%{r}%") for r in region]
        from sqlalchemy import or_
        query = query.filter(or_(*region_filters))
    
    # Apply size filter (multiple values with OR)
    if size:
        size_filters = []
        for s in size:
            size_filters.append(Organization.company_size.ilike(f"%{s}%"))
            size_filters.append(Organization.company_size_2022.ilike(f"%{s}%"))
        from sqlalchemy import or_
        query = query.filter(or_(*size_filters))
    
    # Get total count
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    # Get organizations for current page
    organizations = query.order_by(Organization.name).offset(offset).limit(per_page).all()
    
    # Get unique values for filter checkboxes
    industries = db.query(Organization.main_industry).distinct().filter(Organization.main_industry.isnot(None)).order_by(Organization.main_industry).all()
    industries = [i[0] for i in industries if i[0]]
    
    districts = db.query(Organization.district).distinct().filter(Organization.district.isnot(None)).order_by(Organization.district).all()
    districts = [d[0] for d in districts if d[0]]
    
    regions = db.query(Organization.region).distinct().filter(Organization.region.isnot(None)).order_by(Organization.region).all()
    regions = [r[0] for r in regions if r[0]]
    
    sizes = db.query(Organization.company_size).distinct().filter(Organization.company_size.isnot(None)).order_by(Organization.company_size).all()
    sizes = [s[0] for s in sizes if s[0]]
    
    return templates.TemplateResponse("organizations.html", {
        "request": request,
        "organizations": organizations,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "search": search or "",
        "selected_industries": industry or [],
        "selected_districts": district or [],
        "selected_regions": region or [],
        "selected_sizes": size or [],
        "industries": industries,
        "districts": districts,
        "regions": regions,
        "sizes": sizes,
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
    Show FULL edit form for an organization with ALL data (metrics, taxes, assets, products, meta).
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
    
    return templates.TemplateResponse("organization_edit_full.html", {
        "request": request,
        "org": org,
        "metrics": metrics,
        "taxes": taxes,
        "assets": assets,
        "products": products,
        "meta": meta,
    })


@app.post("/organizations/{organization_id}/edit-full")
async def update_organization_full(
    request: Request,
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Update ALL organization data including metrics, taxes, assets, products, and meta.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        # Get JSON data
        data = await request.json()
        
        # Update organization basic info
        general = data.get('general', {})
        for key, value in general.items():
            if hasattr(org, key):
                setattr(org, key, value)
        
        # Update metrics
        if 'metrics' in data:
            # Delete existing metrics
            db.query(OrganizationMetrics).filter(
                OrganizationMetrics.organization_id == organization_id
            ).delete()
            
            # Add new/updated metrics
            for metric_data in data['metrics']:
                if metric_data.get('year'):  # Only if year is specified
                    metric = OrganizationMetrics(
                        organization_id=organization_id,
                        year=int(metric_data['year']),
                        revenue=float(metric_data['revenue']) if metric_data.get('revenue') else None,
                        profit=float(metric_data['profit']) if metric_data.get('profit') else None,
                        total_employees=int(metric_data['total_employees']) if metric_data.get('total_employees') else None,
                        moscow_employees=int(metric_data['moscow_employees']) if metric_data.get('moscow_employees') else None,
                        total_fot=float(metric_data['total_fot']) if metric_data.get('total_fot') else None,
                        moscow_fot=float(metric_data['moscow_fot']) if metric_data.get('moscow_fot') else None,
                        avg_salary_total=float(metric_data['avg_salary_total']) if metric_data.get('avg_salary_total') else None,
                        avg_salary_moscow=float(metric_data['avg_salary_moscow']) if metric_data.get('avg_salary_moscow') else None,
                        investments=float(metric_data['investments']) if metric_data.get('investments') else None,
                        export_volume=float(metric_data['export_volume']) if metric_data.get('export_volume') else None
                    )
                    db.add(metric)
        
        # Update taxes
        if 'taxes' in data:
            # Delete existing taxes
            db.query(OrganizationTaxes).filter(
                OrganizationTaxes.organization_id == organization_id
            ).delete()
            
            # Add new/updated taxes
            for tax_data in data['taxes']:
                if tax_data.get('year'):
                    tax = OrganizationTaxes(
                        organization_id=organization_id,
                        year=int(tax_data['year']),
                        total_taxes_moscow=float(tax_data['total_taxes_moscow']) if tax_data.get('total_taxes_moscow') else None,
                        profit_tax=float(tax_data['profit_tax']) if tax_data.get('profit_tax') else None,
                        property_tax=float(tax_data['property_tax']) if tax_data.get('property_tax') else None,
                        land_tax=float(tax_data['land_tax']) if tax_data.get('land_tax') else None,
                        ndfl=float(tax_data['ndfl']) if tax_data.get('ndfl') else None,
                        transport_tax=float(tax_data['transport_tax']) if tax_data.get('transport_tax') else None,
                        other_taxes=float(tax_data['other_taxes']) if tax_data.get('other_taxes') else None,
                        excise=float(tax_data['excise']) if tax_data.get('excise') else None
                    )
                    db.add(tax)
        
        # Update assets
        if 'assets' in data:
            # Delete existing assets
            db.query(OrganizationAssets).filter(
                OrganizationAssets.organization_id == organization_id
            ).delete()
            
            # Add new/updated assets
            for asset_data in data['assets']:
                asset = OrganizationAssets(
                    organization_id=organization_id,
                    cadastral_number_land=asset_data.get('cadastral_number_land'),
                    land_area=float(asset_data['land_area']) if asset_data.get('land_area') else None,
                    land_usage=asset_data.get('land_usage'),
                    land_ownership_type=asset_data.get('land_ownership_type'),
                    land_owner=asset_data.get('land_owner'),
                    cadastral_number_building=asset_data.get('cadastral_number_building'),
                    building_area=float(asset_data['building_area']) if asset_data.get('building_area') else None,
                    building_usage=asset_data.get('building_usage'),
                    building_type=asset_data.get('building_type'),
                    building_purpose=asset_data.get('building_purpose'),
                    building_ownership_type=asset_data.get('building_ownership_type'),
                    building_owner=asset_data.get('building_owner'),
                    production_area=float(asset_data['production_area']) if asset_data.get('production_area') else None,
                    property_summary=asset_data.get('property_summary')
                )
                db.add(asset)
        
        # Update products
        if 'products' in data:
            # Delete existing products
            db.query(OrganizationProducts).filter(
                OrganizationProducts.organization_id == organization_id
            ).delete()
            
            # Add new/updated products
            for product_data in data['products']:
                product = OrganizationProducts(
                    organization_id=organization_id,
                    product_name=product_data.get('product_name'),
                    standardized_product=product_data.get('standardized_product'),
                    okpd2_codes=product_data.get('okpd2_codes'),
                    product_types=product_data.get('product_types'),
                    product_catalog=product_data.get('product_catalog'),
                    has_government_orders=product_data.get('has_government_orders', False),
                    capacity_usage=float(product_data['capacity_usage']) if product_data.get('capacity_usage') else None,
                    has_export=product_data.get('has_export', False),
                    export_volume_last_year=float(product_data['export_volume_last_year']) if product_data.get('export_volume_last_year') else None,
                    export_countries=product_data.get('export_countries'),
                    tnved_code=product_data.get('tnved_code')
                )
                db.add(product)
        
        # Update meta
        if 'meta' in data:
            meta_data = data['meta']
            meta = db.query(OrganizationMeta).filter(
                OrganizationMeta.organization_id == organization_id
            ).first()
            
            if meta:
                # Update existing
                for key, value in meta_data.items():
                    if hasattr(meta, key):
                        setattr(meta, key, value)
            else:
                # Create new
                meta = OrganizationMeta(
                    organization_id=organization_id,
                    industry_spark=meta_data.get('industry_spark'),
                    industry_directory=meta_data.get('industry_directory'),
                    presentation_links=meta_data.get('presentation_links'),
                    registry_development=meta_data.get('registry_development'),
                    other_notes=meta_data.get('other_notes')
                )
                db.add(meta)
        
        db.commit()
        logger.info("organization_fully_updated", organization_id=organization_id)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Все данные организации успешно обновлены",
            "organization_id": organization_id
        })
        
    except Exception as e:
        db.rollback()
        logger.error("organization_full_update_failed", organization_id=organization_id, error=str(e))
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
