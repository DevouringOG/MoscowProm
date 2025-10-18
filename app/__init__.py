"""Application package."""
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from typing import Optional
from app.logger import setup_logging, get_logger
from app.db import engine, Base, get_db
from app.db.models import Organization, OrganizationMetrics, OrganizationTaxes, OrganizationAssets, OrganizationProducts, OrganizationMeta
from app.services.excel_processor import process_excel_file
from app.services.fns_api import get_fns_service
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

# Mount static files directory
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Pydantic schema for organization creation
class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""
    inn: str = Field(..., min_length=10, max_length=12, pattern=r"^\d{10,12}$")
    name: str = Field(..., min_length=1, max_length=500)
    full_name: Optional[str] = Field(None, max_length=1000)
    status_spark: Optional[str] = Field(None, max_length=200)
    status_internal: Optional[str] = Field(None, max_length=200)
    status_final: Optional[str] = Field(None, max_length=200)
    legal_address: Optional[str] = Field(None, max_length=1000)
    production_address: Optional[str] = Field(None, max_length=1000)
    additional_address: Optional[str] = Field(None, max_length=1000)
    main_industry: Optional[str] = Field(None, max_length=200)
    main_subindustry: Optional[str] = Field(None, max_length=200)
    extra_industry: Optional[str] = Field(None, max_length=200)
    extra_subindustry: Optional[str] = Field(None, max_length=200)
    main_okved: Optional[str] = Field(None, max_length=100)
    main_okved_name: Optional[str] = Field(None, max_length=200)
    prod_okved: Optional[str] = Field(None, max_length=100)
    prod_okved_name: Optional[str] = Field(None, max_length=200)
    company_info: Optional[str] = None
    company_size: Optional[str] = Field(None, max_length=100)
    head_name: Optional[str] = Field(None, max_length=200)
    parent_org_name: Optional[str] = Field(None, max_length=500)
    parent_org_inn: Optional[str] = Field(None, max_length=12)
    head_contacts: Optional[str] = Field(None, max_length=500)
    head_email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=100)
    emergency_contact: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=300)
    email: Optional[str] = Field(None, max_length=200)
    district: Optional[str] = Field(None, max_length=200)
    region: Optional[str] = Field(None, max_length=200)



@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload page."""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/organizations/create", response_class=HTMLResponse)
async def create_organization_page(request: Request):
    """Organization creation page."""
    return templates.TemplateResponse("organization_create.html", {"request": request})


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
        error_msg = str(e)
        
        # Улучшенные сообщения об ошибках
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
        # Clean up uploaded file
        try:
            file_path.unlink()
        except Exception as e:
            logger.error("file_cleanup_failed", error=str(e))


@app.post("/api/organizations")
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new organization manually.
    """
    try:
        # Check if organization with this INN already exists
        existing = db.query(Organization).filter(Organization.inn == org_data.inn).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"ОШИБКА: Предприятие с ИНН {org_data.inn} уже существует в базе"
            )
        
        # Create new organization
        new_org = Organization(**org_data.model_dump())
        db.add(new_org)
        db.commit()
        db.refresh(new_org)
        
        logger.info(
            "organization_created_manually",
            organization_id=new_org.id,
            inn=new_org.inn,
            name=new_org.name
        )
        
        return JSONResponse(content={
            "success": True,
            "message": f"Предприятие '{new_org.name}' успешно создано",
            "organization_id": new_org.id,
            "inn": new_org.inn,
            "name": new_org.name
        })
        
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)
        
        if 'unique constraint' in error_msg.lower() or 'duplicate key' in error_msg.lower():
            user_message = f"ОШИБКА: Предприятие с ИНН {org_data.inn} уже существует"
        else:
            user_message = f"ОШИБКА: Нарушение целостности базы данных"
        
        logger.error("organization_creation_failed", error=error_msg)
        raise HTTPException(status_code=400, detail=user_message)
        
    except HTTPException:
        raise
        
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error("organization_creation_failed", error=error_msg)
        raise HTTPException(
            status_code=500, 
            detail=f"ОШИБКА: Не удалось создать предприятие. {error_msg[:100]}"
        )


@app.get("/organizations", response_class=HTMLResponse)
async def list_organizations(
    request: Request,
    page: int = 1,
    search: str = None,
    industry: list[str] = Query(None),
    district: list[str] = Query(None),
    region: list[str] = Query(None),
    size: list[str] = Query(None),
    sort_by: str = Query("name", regex="^(name|inn|main_industry|status_final|district|region|company_size)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
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
    
    # Apply sorting
    sort_field = getattr(Organization, sort_by, Organization.name)
    if order == "desc":
        from sqlalchemy import desc
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)
    
    # Get organizations for current page
    organizations = query.offset(offset).limit(per_page).all()
    
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
        "sort_by": sort_by,
        "order": order,
    })


@app.get("/organizations/{organization_id}/analytics", response_class=HTMLResponse)
async def organization_analytics(
    request: Request,
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Detailed analytics page for a specific organization.
    """
    from sqlalchemy import func, desc
    
    # Get organization
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get all metrics ordered by year
    all_metrics = db.query(OrganizationMetrics).filter(
        OrganizationMetrics.organization_id == organization_id
    ).order_by(OrganizationMetrics.year).all()
    
    # Get latest year metrics
    latest_year = db.query(func.max(OrganizationMetrics.year)).filter(
        OrganizationMetrics.organization_id == organization_id
    ).scalar() or datetime.now().year
    
    latest_metrics = db.query(OrganizationMetrics).filter(
        OrganizationMetrics.organization_id == organization_id,
        OrganizationMetrics.year == latest_year
    ).first()
    
    # Calculate trends
    prev_year_metrics = db.query(OrganizationMetrics).filter(
        OrganizationMetrics.organization_id == organization_id,
        OrganizationMetrics.year == latest_year - 1
    ).first()
    
    revenue_trend = None
    employees_trend = None
    
    if latest_metrics and prev_year_metrics:
        if prev_year_metrics.revenue and latest_metrics.revenue:
            change = ((latest_metrics.revenue - prev_year_metrics.revenue) / prev_year_metrics.revenue) * 100
            revenue_trend = {
                'change': f"{'↑' if change > 0 else '↓'} {abs(change):.1f}%",
                'direction': 'up' if change > 0 else 'down' if change < 0 else 'neutral'
            }
        
        if prev_year_metrics.total_employees and latest_metrics.total_employees:
            change = ((latest_metrics.total_employees - prev_year_metrics.total_employees) / prev_year_metrics.total_employees) * 100
            employees_trend = {
                'change': f"{'↑' if change > 0 else '↓'} {abs(change):.1f}%",
                'direction': 'up' if change > 0 else 'down' if change < 0 else 'neutral'
            }
    
    # Prepare metrics data for charts
    metrics_data = [
        {
            'year': m.year,
            'revenue': float(m.revenue or 0),
            'profit': float(m.profit or 0),
            'total_employees': int(m.total_employees or 0),
            'moscow_employees': int(m.moscow_employees or 0),
            'avg_salary_total': float(m.avg_salary_total or 0),
            'avg_salary_moscow': float(m.avg_salary_moscow or 0),
            'investments': float(m.investments or 0),
            'export_volume': float(m.export_volume or 0)
        }
        for m in all_metrics
    ]
    
    # Get taxes data
    all_taxes = db.query(OrganizationTaxes).filter(
        OrganizationTaxes.organization_id == organization_id
    ).order_by(OrganizationTaxes.year).all()
    
    taxes_data = [
        {
            'year': t.year,
            'total_taxes': float(t.total_taxes_moscow or 0),
            'profit_tax': float(t.profit_tax or 0),
            'property_tax': float(t.property_tax or 0),
            'ndfl': float(t.ndfl or 0)
        }
        for t in all_taxes
    ]
    
    # Industry comparison
    industry_comparison = []
    if org.main_industry:
        industry_orgs = db.query(
            Organization.id,
            Organization.name,
            func.max(OrganizationMetrics.revenue).label('revenue'),
            func.max(OrganizationMetrics.profit).label('profit'),
            func.max(OrganizationMetrics.total_employees).label('employees'),
            func.max(OrganizationMetrics.avg_salary_total).label('avg_salary')
        ).join(
            OrganizationMetrics,
            Organization.id == OrganizationMetrics.organization_id
        ).filter(
            Organization.main_industry == org.main_industry,
            OrganizationMetrics.year == latest_year
        ).group_by(
            Organization.id,
            Organization.name
        ).order_by(
            desc('revenue')
        ).limit(10).all()
        
        industry_comparison = [
            {
                'id': org_id,
                'name': name,
                'revenue': float(revenue or 0),
                'profit': float(profit or 0),
                'employees': int(employees or 0) if employees else None,
                'avg_salary': float(avg_salary or 0) if avg_salary else None
            }
            for org_id, name, revenue, profit, employees, avg_salary in industry_orgs
        ]
    
    return templates.TemplateResponse(
        "organization_analytics.html",
        {
            "request": request,
            "organization": org,
            "latest_year": latest_year,
            "latest_metrics": latest_metrics or {},
            "all_metrics": all_metrics,
            "metrics_data": metrics_data,
            "taxes_data": taxes_data,
            "revenue_trend": revenue_trend,
            "employees_trend": employees_trend,
            "industry_comparison": industry_comparison
        }
    )


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


@app.post("/organizations/{organization_id}/update-from-fns")
async def update_organization_from_fns(
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Update organization data from FNS API using INN.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not org.inn:
        raise HTTPException(status_code=400, detail="Organization has no INN")
    
    try:
        # Check if FNS API is enabled
        fns_enabled = getattr(settings.get('fns_api', {}), 'enabled', False)
        if not fns_enabled:
            raise HTTPException(status_code=503, detail="FNS API is disabled")
        
        # Get FNS API configuration
        fns_config = settings.get('fns_api', {})
        api_key = getattr(fns_config, 'api_key', None)
        timeout = getattr(fns_config, 'timeout', 30)
        
        if not api_key:
            raise HTTPException(status_code=503, detail="FNS API key not configured")
        
        # Get FNS service
        fns_service = get_fns_service(api_key=api_key, timeout=timeout)
        
        # Fetch data from FNS
        logger.info("fetching_fns_data", organization_id=organization_id, inn=org.inn)
        fns_data = await fns_service.get_organization_by_inn(org.inn)
        
        if not fns_data:
            raise HTTPException(status_code=404, detail="Organization not found in FNS database")
        
        # Track what was updated
        updated_fields = []
        
        # Update organization fields - only fields that exist in the model
        # Map: model_field -> fns_field
        field_mapping = {
            'name': 'name',
            'full_name': 'full_name',
            'legal_address': 'legal_address',
            'status_final': 'status',  # FNS 'status' maps to 'status_final' in our model
            'main_okved': 'main_okved',
            'main_okved_name': 'main_okved_name',
            'head_name': 'head_name',
            'registration_date': 'registration_date'
        }
        
        for org_field, fns_field in field_mapping.items():
            if fns_field in fns_data and fns_data[fns_field]:
                # Check if field exists in model
                if not hasattr(org, org_field):
                    continue
                    
                old_value = getattr(org, org_field, None)
                new_value = fns_data[fns_field]
                
                # Only update if value changed
                if old_value != new_value:
                    setattr(org, org_field, new_value)
                    updated_fields.append(org_field)
                    logger.debug("field_updated", field=org_field, old_value=old_value, new_value=new_value)
        
        # Update updated_at timestamp
        org.updated_at = datetime.now()
        
        db.commit()
        logger.info("organization_updated_from_fns", 
                   organization_id=organization_id, 
                   inn=org.inn,
                   updated_fields=updated_fields)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Данные обновлены из ФНС. Обновлено полей: {len(updated_fields)}",
            "organization_id": organization_id,
            "updated_fields": updated_fields,
            "inn": org.inn
        })
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("fns_update_failed", 
                    organization_id=organization_id, 
                    inn=org.inn,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update from FNS: {str(e)}")


@app.post("/organizations/{organization_id}/import-financials")
async def import_financials_from_fns(
    organization_id: int,
    db: Session = Depends(get_db)
):
    """
    Import financial statements from FNS API and populate metrics table.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not org.inn:
        raise HTTPException(status_code=400, detail="Organization has no INN")
    
    # Check INN length - financial statements only available for legal entities (10 digits)
    if len(org.inn) != 10:
        raise HTTPException(status_code=400, detail="Financial statements are only available for legal entities (ЮЛ)")
    
    try:
        # Check if FNS API is enabled
        fns_enabled = getattr(settings.get('fns_api', {}), 'enabled', False)
        if not fns_enabled:
            raise HTTPException(status_code=503, detail="FNS API is disabled")
        
        # Get FNS API configuration
        fns_config = settings.get('fns_api', {})
        api_key = getattr(fns_config, 'api_key', None)
        timeout = getattr(fns_config, 'timeout', 30)
        
        if not api_key:
            raise HTTPException(status_code=503, detail="FNS API key not configured")
        
        # Get FNS service
        fns_service = get_fns_service(api_key=api_key, timeout=timeout)
        
        # Fetch financial statements from FNS
        logger.info("fetching_fns_financials", organization_id=organization_id, inn=org.inn)
        financial_data = await fns_service.get_financial_statements(org.inn)
        
        if not financial_data:
            raise HTTPException(status_code=404, detail="Financial statements not found in FNS database")
        
        # Process financial data and update metrics
        imported_years = []
        updated_years = []
        
        for year_str, year_data in financial_data.items():
            try:
                year = int(year_str)
            except ValueError:
                continue
            
            # Check if metrics for this year already exist
            existing_metric = db.query(OrganizationMetrics).filter(
                OrganizationMetrics.organization_id == organization_id,
                OrganizationMetrics.year == year
            ).first()
            
            # Extract financial data from FNS codes
            # Форма 1 (Бухгалтерский баланс)
            # Форма 2 (Отчет о финансовых результатах)
            revenue = year_data.get('2110')  # Выручка
            profit = year_data.get('2400')   # Чистая прибыль
            
            if existing_metric:
                # Update existing
                if revenue is not None:
                    existing_metric.revenue = float(revenue) * 1000  # Convert from thousands to rubles
                if profit is not None:
                    existing_metric.profit = float(profit) * 1000
                updated_years.append(year)
            else:
                # Create new
                new_metric = OrganizationMetrics(
                    organization_id=organization_id,
                    year=year,
                    revenue=float(revenue) * 1000 if revenue is not None else None,
                    profit=float(profit) * 1000 if profit is not None else None
                )
                db.add(new_metric)
                imported_years.append(year)
        
        db.commit()
        logger.info("financials_imported_from_fns", 
                   organization_id=organization_id, 
                   inn=org.inn,
                   imported_years=imported_years,
                   updated_years=updated_years)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Бухгалтерская отчётность импортирована из ФНС",
            "organization_id": organization_id,
            "imported_years": sorted(imported_years),
            "updated_years": sorted(updated_years),
            "total_years": len(imported_years) + len(updated_years),
            "inn": org.inn
        })
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("financials_import_failed", 
                    organization_id=organization_id, 
                    inn=org.inn,
                    error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to import financials from FNS: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root_redirect():
    """Redirect root to analytics."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/analytics")


@app.get("/analytics", response_class=HTMLResponse)
async def analytics(
    request: Request,
    db: Session = Depends(get_db),
    industries: list[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    company_sizes: list[str] = Query(None),
    districts: list[str] = Query(None),
):
    """
    Analytics dashboard with metrics, charts and visualizations.
    Supports filtering by multiple industries, year range, company sizes, and districts.
    """
    from sqlalchemy import func, desc, and_, or_
    
    try:
        # Build base query with filters
        org_filter = []
        metrics_filter = []
        
        # Multi-select filters
        if industries:
            org_filter.append(Organization.main_industry.in_(industries))
        if company_sizes:
            org_filter.append(Organization.company_size.in_(company_sizes))
        if districts:
            org_filter.append(Organization.district.in_(districts))
        
        # Year range filter
        if year_from:
            metrics_filter.append(OrganizationMetrics.year >= year_from)
        if year_to:
            metrics_filter.append(OrganizationMetrics.year <= year_to)
        
        # Get available filter options
        all_industries = db.query(
            func.distinct(Organization.main_industry)
        ).filter(
            Organization.main_industry.isnot(None)
        ).order_by(Organization.main_industry).all()
        all_industries = [ind[0] for ind in all_industries if ind[0]]
        
        all_years = db.query(
            func.distinct(OrganizationMetrics.year)
        ).order_by(
            OrganizationMetrics.year
        ).all()
        all_years = [year[0] for year in all_years if year[0]]
        
        all_company_sizes = db.query(
            func.distinct(Organization.company_size)
        ).filter(
            Organization.company_size.isnot(None)
        ).order_by(Organization.company_size).all()
        all_company_sizes = [size[0] for size in all_company_sizes if size[0]]
        
        all_districts = db.query(
            func.distinct(Organization.district)
        ).filter(
            Organization.district.isnot(None)
        ).order_by(Organization.district).all()
        all_districts = [dist[0] for dist in all_districts if dist[0]]
        
        # Determine year range for queries
        if not year_from and all_years:
            year_from = min(all_years)
        if not year_to and all_years:
            year_to = max(all_years)
        
        latest_year = year_to or datetime.now().year
        
        # Summary statistics
        org_query = db.query(Organization)
        if org_filter:
            org_query = org_query.filter(and_(*org_filter))
        total_organizations = org_query.count()
        
        # Total revenue for latest year
        revenue_query = db.query(func.sum(OrganizationMetrics.revenue)).join(
            Organization
        ).filter(OrganizationMetrics.year == latest_year)
        if org_filter:
            revenue_query = revenue_query.filter(and_(*org_filter))
        total_revenue = revenue_query.scalar() or 0
        
        # Previous year revenue for comparison
        prev_revenue_query = db.query(func.sum(OrganizationMetrics.revenue)).join(
            Organization
        ).filter(OrganizationMetrics.year == latest_year - 1)
        if org_filter:
            prev_revenue_query = prev_revenue_query.filter(and_(*org_filter))
        prev_year_revenue = prev_revenue_query.scalar() or 0
        
        revenue_change = 0
        if prev_year_revenue > 0:
            revenue_change = ((total_revenue - prev_year_revenue) / prev_year_revenue) * 100
        
        # Total employees
        employees_query = db.query(func.sum(OrganizationMetrics.total_employees)).join(
            Organization
        ).filter(OrganizationMetrics.year == latest_year)
        if org_filter:
            employees_query = employees_query.filter(and_(*org_filter))
        total_employees = employees_query.scalar() or 0
        
        # Total investments
        investments_query = db.query(func.sum(OrganizationMetrics.investments)).join(
            Organization
        ).filter(OrganizationMetrics.year == latest_year)
        if org_filter:
            investments_query = investments_query.filter(and_(*org_filter))
        total_investments = investments_query.scalar() or 0
        
        # Total export
        export_query = db.query(func.sum(OrganizationMetrics.export_volume)).join(
            Organization
        ).filter(OrganizationMetrics.year == latest_year)
        if org_filter:
            export_query = export_query.filter(and_(*org_filter))
        total_export = export_query.scalar() or 0
        
        # Total taxes
        taxes_query = db.query(func.sum(OrganizationTaxes.total_taxes_moscow)).join(
            Organization
        ).filter(OrganizationTaxes.year == latest_year)
        if org_filter:
            taxes_query = taxes_query.filter(and_(*org_filter))
        total_taxes = taxes_query.scalar() or 0
        
        # Average salary
        avg_salary_query = db.query(func.avg(OrganizationMetrics.avg_salary_total)).join(
            Organization
        ).filter(OrganizationMetrics.year == latest_year)
        if org_filter:
            avg_salary_query = avg_salary_query.filter(and_(*org_filter))
        avg_salary = avg_salary_query.scalar() or 0
        
        # Revenue by year
        revenue_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.revenue).label('revenue')
        ).join(Organization)
        if org_filter:
            revenue_by_year_query = revenue_by_year_query.filter(and_(*org_filter))
        if metrics_filter:
            revenue_by_year_query = revenue_by_year_query.filter(and_(*metrics_filter))
        revenue_by_year = revenue_by_year_query.group_by(
            OrganizationMetrics.year
        ).order_by(OrganizationMetrics.year).all()
        
        revenue_by_year_data = [
            {'year': year, 'revenue': float(revenue or 0)}
            for year, revenue in revenue_by_year
        ]
        
        # Employees by year
        employees_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.total_employees).label('employees')
        ).join(Organization)
        if org_filter:
            employees_by_year_query = employees_by_year_query.filter(and_(*org_filter))
        if metrics_filter:
            employees_by_year_query = employees_by_year_query.filter(and_(*metrics_filter))
        employees_by_year = employees_by_year_query.group_by(
            OrganizationMetrics.year
        ).order_by(OrganizationMetrics.year).all()
        
        employees_by_year_data = [
            {'year': year, 'employees': int(employees or 0)}
            for year, employees in employees_by_year
        ]
        
        # Investments by year
        investments_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.investments).label('investments')
        ).join(Organization)
        if org_filter:
            investments_by_year_query = investments_by_year_query.filter(and_(*org_filter))
        if metrics_filter:
            investments_by_year_query = investments_by_year_query.filter(and_(*metrics_filter))
        investments_by_year = investments_by_year_query.group_by(
            OrganizationMetrics.year
        ).order_by(OrganizationMetrics.year).all()
        
        investments_by_year_data = [
            {'year': year, 'investments': float(investments or 0)}
            for year, investments in investments_by_year
        ]
        
        # Export by year
        export_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.export_volume).label('export_volume')
        ).join(Organization)
        if org_filter:
            export_by_year_query = export_by_year_query.filter(and_(*org_filter))
        if metrics_filter:
            export_by_year_query = export_by_year_query.filter(and_(*metrics_filter))
        export_by_year = export_by_year_query.group_by(
            OrganizationMetrics.year
        ).order_by(OrganizationMetrics.year).all()
        
        export_by_year_data = [
            {'year': year, 'export': float(export_volume or 0)}
            for year, export_volume in export_by_year
        ]
        
        # Taxes by year
        taxes_by_year_query = db.query(
            OrganizationTaxes.year,
            func.sum(OrganizationTaxes.total_taxes_moscow).label('taxes')
        ).join(Organization)
        if org_filter:
            taxes_by_year_query = taxes_by_year_query.filter(and_(*org_filter))
        if metrics_filter:
            taxes_by_year_query = taxes_by_year_query.filter(and_(*metrics_filter))
        taxes_by_year = taxes_by_year_query.group_by(
            OrganizationTaxes.year
        ).order_by(OrganizationTaxes.year).all()
        
        taxes_by_year_data = [
            {'year': year, 'taxes': float(taxes or 0)}
            for year, taxes in taxes_by_year
        ]
        
        # Average salary by year
        salary_by_year_query = db.query(
            OrganizationMetrics.year,
            func.avg(OrganizationMetrics.avg_salary_total).label('avg_salary')
        ).join(Organization)
        if org_filter:
            salary_by_year_query = salary_by_year_query.filter(and_(*org_filter))
        if metrics_filter:
            salary_by_year_query = salary_by_year_query.filter(and_(*metrics_filter))
        salary_by_year = salary_by_year_query.group_by(
            OrganizationMetrics.year
        ).order_by(OrganizationMetrics.year).all()
        
        salary_by_year_data = [
            {'year': year, 'salary': float(avg_salary or 0)}
            for year, avg_salary in salary_by_year
        ]
        
        # Revenue by industry (for current filters and latest year)
        revenue_by_industry_query = db.query(
            Organization.main_industry,
            func.sum(OrganizationMetrics.revenue).label('revenue')
        ).join(
            OrganizationMetrics
        ).filter(
            Organization.main_industry.isnot(None),
            OrganizationMetrics.year == latest_year
        )
        if org_filter:
            revenue_by_industry_query = revenue_by_industry_query.filter(and_(*org_filter))
        revenue_by_industry = revenue_by_industry_query.group_by(
            Organization.main_industry
        ).order_by(desc('revenue')).limit(10).all()
        
        revenue_by_industry_data = [
            {'industry': ind or 'Не указано', 'revenue': float(rev or 0)}
            for ind, rev in revenue_by_industry
        ]
        
        # Top organizations by revenue
        top_orgs_query = db.query(
            Organization.id,
            Organization.name,
            Organization.main_industry,
            func.sum(OrganizationMetrics.revenue).label('revenue'),
            func.sum(OrganizationMetrics.total_employees).label('employees'),
            func.avg(OrganizationMetrics.avg_salary_total).label('avg_salary')
        ).join(OrganizationMetrics)
        if org_filter:
            top_orgs_query = top_orgs_query.filter(and_(*org_filter))
        if metrics_filter:
            top_orgs_query = top_orgs_query.filter(and_(*metrics_filter))
        top_orgs = top_orgs_query.group_by(
            Organization.id,
            Organization.name,
            Organization.main_industry
        ).order_by(desc('revenue')).limit(10).all()
        
        top_organizations = [
            {
                'id': org_id,
                'name': name,
                'main_industry': industry or 'Не указано',
                'revenue': float(revenue or 0),
                'employees': int(employees or 0) if employees else 0,
                'avg_salary': float(avg_salary or 0) if avg_salary else 0
            }
            for org_id, name, industry, revenue, employees, avg_salary in top_orgs
        ]
        
        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "summary": {
                    "total_organizations": total_organizations,
                    "total_revenue": total_revenue,
                    "revenue_change": revenue_change,
                    "total_employees": int(total_employees),
                    "total_investments": total_investments,
                    "total_export": total_export,
                    "total_taxes": total_taxes,
                    "avg_salary": avg_salary,
                },
                "revenue_by_year": revenue_by_year_data,
                "employees_by_year": employees_by_year_data,
                "investments_by_year": investments_by_year_data,
                "export_by_year": export_by_year_data,
                "taxes_by_year": taxes_by_year_data,
                "salary_by_year": salary_by_year_data,
                "revenue_by_industry": revenue_by_industry_data,
                "top_organizations": top_organizations,
                # Filter options
                "all_industries": all_industries,
                "all_years": all_years,
                "all_company_sizes": all_company_sizes,
                "all_districts": all_districts,
                # Current filter values
                "selected_industries": industries or [],
                "selected_year_from": year_from,
                "selected_year_to": year_to,
                "selected_company_sizes": company_sizes or [],
                "selected_districts": districts or [],
            }
        )
        
    except Exception as e:
        logger.error("analytics_page_failed", error=str(e))
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


@app.get("/api/fns/organization/{inn}")
async def get_organization_from_fns(inn: str):
    """
    Fetch organization data from FNS by INN for form auto-fill.
    """
    try:
        # Validate INN format
        if not inn or not inn.isdigit() or len(inn) not in [10, 12]:
            raise HTTPException(status_code=400, detail="Invalid INN format. Must be 10 or 12 digits.")
        
        # Check if FNS API is enabled
        fns_enabled = getattr(settings.get('fns_api', {}), 'enabled', False)
        if not fns_enabled:
            raise HTTPException(status_code=503, detail="FNS API is disabled")
        
        # Get FNS API configuration
        fns_config = settings.get('fns_api', {})
        api_key = getattr(fns_config, 'api_key', None)
        timeout = getattr(fns_config, 'timeout', 30)
        
        if not api_key:
            raise HTTPException(status_code=503, detail="FNS API key not configured")
        
        # Get FNS service
        fns_service = get_fns_service(api_key=api_key, timeout=timeout)
        
        # Fetch data from FNS
        logger.info("fetching_fns_data_for_form", inn=inn)
        fns_data = await fns_service.get_organization_by_inn(inn)
        
        if not fns_data:
            raise HTTPException(status_code=404, detail="Organization not found in FNS database")
        
        logger.info("fns_data_fetched_for_form", inn=inn, name=fns_data.get('name'))
        
        return JSONResponse(content={
            "status": "success",
            "message": "Organization data fetched from FNS",
            "data": fns_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("fns_data_fetch_failed", inn=inn, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from FNS: {str(e)}")
