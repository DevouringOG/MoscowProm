from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, or_
from app.db import get_db
from app.db.models import (
    Organization,
    OrganizationMetrics,
    OrganizationTaxes,
    OrganizationAssets,
    OrganizationProducts,
    OrganizationMeta,
)
from app.schemas import OrganizationCreate
from app.services.excel_exporter import export_organizations_to_excel
from app.dependencies.templates import templates
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_class=HTMLResponse)
async def list_organizations(
    request: Request,
    page: int = 1,
    search: str = None,
    industry: list[str] = Query(None),
    district: list[str] = Query(None),
    region: list[str] = Query(None),
    size: list[str] = Query(None),
    sort_by: str = Query(
        "name",
        regex="^(name|inn|main_industry|status_final|district|region|company_size)$",
    ),
    order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    per_page = 20
    offset = (page - 1) * per_page

    query = db.query(Organization)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Organization.name.ilike(search_filter))
            | (Organization.inn.ilike(search_filter))
        )

    if industry:
        industry_filters = []
        for ind in industry:
            industry_filters.append(
                Organization.main_industry.ilike(f"%{ind}%")
            )
            industry_filters.append(
                Organization.extra_industry.ilike(f"%{ind}%")
            )
        query = query.filter(or_(*industry_filters))

    if district:
        district_filters = [
            Organization.district.ilike(f"%{d}%") for d in district
        ]
        query = query.filter(or_(*district_filters))

    if region:
        region_filters = [Organization.region.ilike(f"%{r}%") for r in region]
        query = query.filter(or_(*region_filters))

    if size:
        size_filters = []
        for s in size:
            size_filters.append(Organization.company_size.ilike(f"%{s}%"))
            size_filters.append(Organization.company_size_2022.ilike(f"%{s}%"))
        query = query.filter(or_(*size_filters))

    total = query.count()
    total_pages = (total + per_page - 1) // per_page

    sort_field = getattr(Organization, sort_by, Organization.name)
    if order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    organizations = query.offset(offset).limit(per_page).all()

    industries = (
        db.query(Organization.main_industry)
        .distinct()
        .filter(Organization.main_industry.isnot(None))
        .order_by(Organization.main_industry)
        .all()
    )
    industries = [i[0] for i in industries if i[0]]

    districts = (
        db.query(Organization.district)
        .distinct()
        .filter(Organization.district.isnot(None))
        .order_by(Organization.district)
        .all()
    )
    districts = [d[0] for d in districts if d[0]]

    regions = (
        db.query(Organization.region)
        .distinct()
        .filter(Organization.region.isnot(None))
        .order_by(Organization.region)
        .all()
    )
    regions = [r[0] for r in regions if r[0]]

    sizes = (
        db.query(Organization.company_size)
        .distinct()
        .filter(Organization.company_size.isnot(None))
        .order_by(Organization.company_size)
        .all()
    )
    sizes = [s[0] for s in sizes if s[0]]

    return templates.TemplateResponse(
        "organizations.html",
        {
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
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_organization_page(request: Request):
    return templates.TemplateResponse(
        "organization_create.html", {"request": request}
    )


@router.post("", status_code=201)
async def create_organization(
    org_data: OrganizationCreate, db: Session = Depends(get_db)
):
    try:
        existing = (
            db.query(Organization)
            .filter(Organization.inn == org_data.inn)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"ОШИБКА: Предприятие с ИНН {org_data.inn} уже существует в базе",
            )

        new_org = Organization(**org_data.model_dump())
        db.add(new_org)
        db.commit()
        db.refresh(new_org)

        logger.info(
            "organization_created", organization_id=new_org.id, inn=new_org.inn
        )

        return JSONResponse(
            content={
                "success": True,
                "message": f"Предприятие '{new_org.name}' успешно создано",
                "organization_id": new_org.id,
                "inn": new_org.inn,
                "name": new_org.name,
            }
        )

    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig)

        if (
            "unique constraint" in error_msg.lower()
            or "duplicate key" in error_msg.lower()
        ):
            user_message = (
                f"ОШИБКА: Предприятие с ИНН {org_data.inn} уже существует"
            )
        else:
            user_message = "ОШИБКА: Нарушение целостности базы данных"

        logger.error("organization_creation_failed", error=error_msg)
        raise HTTPException(status_code=400, detail=user_message)

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.error("organization_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"ОШИБКА: {str(e)[:100]}")


@router.get("/export")
async def export_organizations(
    search: str = None,
    industry: list[str] = Query(None),
    district: list[str] = Query(None),
    region: list[str] = Query(None),
    size: list[str] = Query(None),
    sort_by: str = Query("name"),
    order: str = Query("asc"),
    db: Session = Depends(get_db),
):
    try:
        query = db.query(Organization)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Organization.name.ilike(search_filter))
                | (Organization.inn.ilike(search_filter))
            )

        if industry:
            industry_filters = []
            for ind in industry:
                industry_filters.append(
                    Organization.main_industry.ilike(f"%{ind}%")
                )
                industry_filters.append(
                    Organization.extra_industry.ilike(f"%{ind}%")
                )
            query = query.filter(or_(*industry_filters))

        if district:
            district_filters = [
                Organization.district.ilike(f"%{d}%") for d in district
            ]
            query = query.filter(or_(*district_filters))

        if region:
            region_filters = [
                Organization.region.ilike(f"%{r}%") for r in region
            ]
            query = query.filter(or_(*region_filters))

        if size:
            size_filters = []
            for s in size:
                size_filters.append(Organization.company_size.ilike(f"%{s}%"))
                size_filters.append(
                    Organization.company_size_2022.ilike(f"%{s}%")
                )
            query = query.filter(or_(*size_filters))

        sort_field = getattr(Organization, sort_by, Organization.name)
        if order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(sort_field)

        organizations = query.all()

        if not organizations:
            raise HTTPException(
                status_code=404, detail="Нет данных для экспорта"
            )

        excel_file = export_organizations_to_excel(organizations, db)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"predpriyatiya_{timestamp}.xlsx"

        logger.info("organizations_exported", count=len(organizations))

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("export_failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"ОШИБКА ЭКСПОРТА: {str(e)[:200]}"
        )


@router.get("/{organization_id}", response_class=HTMLResponse)
async def view_organization(
    request: Request, organization_id: int, db: Session = Depends(get_db)
):
    org = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    metrics = (
        db.query(OrganizationMetrics)
        .filter(OrganizationMetrics.organization_id == organization_id)
        .order_by(OrganizationMetrics.year)
        .all()
    )

    taxes = (
        db.query(OrganizationTaxes)
        .filter(OrganizationTaxes.organization_id == organization_id)
        .order_by(OrganizationTaxes.year)
        .all()
    )

    assets = (
        db.query(OrganizationAssets)
        .filter(OrganizationAssets.organization_id == organization_id)
        .all()
    )

    products = (
        db.query(OrganizationProducts)
        .filter(OrganizationProducts.organization_id == organization_id)
        .all()
    )

    meta = (
        db.query(OrganizationMeta)
        .filter(OrganizationMeta.organization_id == organization_id)
        .first()
    )

    return templates.TemplateResponse(
        "organization_detail.html",
        {
            "request": request,
            "org": org,
            "metrics": metrics,
            "taxes": taxes,
            "assets": assets,
            "products": products,
            "meta": meta,
        },
    )


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: int, db: Session = Depends(get_db)
):
    org = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        db.delete(org)
        db.commit()
        logger.info("organization_deleted", organization_id=organization_id)

        return JSONResponse(
            content={
                "status": "success",
                "message": "Организация успешно удалена",
            }
        )

    except Exception as e:
        db.rollback()
        logger.error(
            "organization_delete_failed",
            organization_id=organization_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))
