from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db import get_db
from app.db.models import (
    Organization,
    OrganizationMetrics,
    OrganizationTaxes,
    OrganizationAssets,
    OrganizationProducts,
    OrganizationMeta,
)
from app.services.fns_api import get_fns_service
from app.dependencies.templates import templates
from app.logger import get_logger
from config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/organizations", tags=["organization-analytics"])


@router.get("/{organization_id}/analytics", response_class=HTMLResponse)
async def organization_analytics(
    request: Request, organization_id: int, db: Session = Depends(get_db)
):
    org = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    all_metrics = (
        db.query(OrganizationMetrics)
        .filter(OrganizationMetrics.organization_id == organization_id)
        .order_by(OrganizationMetrics.year)
        .all()
    )

    latest_year = (
        db.query(func.max(OrganizationMetrics.year))
        .filter(OrganizationMetrics.organization_id == organization_id)
        .scalar()
        or datetime.now().year
    )

    latest_metrics = (
        db.query(OrganizationMetrics)
        .filter(
            OrganizationMetrics.organization_id == organization_id,
            OrganizationMetrics.year == latest_year,
        )
        .first()
    )

    prev_year_metrics = (
        db.query(OrganizationMetrics)
        .filter(
            OrganizationMetrics.organization_id == organization_id,
            OrganizationMetrics.year == latest_year - 1,
        )
        .first()
    )

    revenue_trend = None
    employees_trend = None

    if latest_metrics and prev_year_metrics:
        if prev_year_metrics.revenue and latest_metrics.revenue:
            change = (
                (latest_metrics.revenue - prev_year_metrics.revenue)
                / prev_year_metrics.revenue
            ) * 100
            revenue_trend = {
                "change": f"{'↑' if change > 0 else '↓'} {abs(change):.1f}%",
                "direction": (
                    "up" if change > 0 else "down" if change < 0 else "neutral"
                ),
            }

        if (
            prev_year_metrics.total_employees
            and latest_metrics.total_employees
        ):
            change = (
                (
                    latest_metrics.total_employees
                    - prev_year_metrics.total_employees
                )
                / prev_year_metrics.total_employees
            ) * 100
            employees_trend = {
                "change": f"{'↑' if change > 0 else '↓'} {abs(change):.1f}%",
                "direction": (
                    "up" if change > 0 else "down" if change < 0 else "neutral"
                ),
            }

    metrics_data = [
        {
            "year": m.year,
            "revenue": float(m.revenue or 0),
            "profit": float(m.profit or 0),
            "total_employees": int(m.total_employees or 0),
            "moscow_employees": int(m.moscow_employees or 0),
            "avg_salary_total": float(m.avg_salary_total or 0),
            "avg_salary_moscow": float(m.avg_salary_moscow or 0),
            "investments": float(m.investments or 0),
            "export_volume": float(m.export_volume or 0),
        }
        for m in all_metrics
    ]

    all_taxes = (
        db.query(OrganizationTaxes)
        .filter(OrganizationTaxes.organization_id == organization_id)
        .order_by(OrganizationTaxes.year)
        .all()
    )

    taxes_data = [
        {
            "year": t.year,
            "total_taxes": float(t.total_taxes_moscow or 0),
            "profit_tax": float(t.profit_tax or 0),
            "property_tax": float(t.property_tax or 0),
            "ndfl": float(t.ndfl or 0),
        }
        for t in all_taxes
    ]

    industry_comparison = []
    if org.main_industry:
        industry_orgs = (
            db.query(
                Organization.id,
                Organization.name,
                func.max(OrganizationMetrics.revenue).label("revenue"),
                func.max(OrganizationMetrics.profit).label("profit"),
                func.max(OrganizationMetrics.total_employees).label(
                    "employees"
                ),
                func.max(OrganizationMetrics.avg_salary_total).label(
                    "avg_salary"
                ),
            )
            .join(
                OrganizationMetrics,
                Organization.id == OrganizationMetrics.organization_id,
            )
            .filter(
                Organization.main_industry == org.main_industry,
                OrganizationMetrics.year == latest_year,
            )
            .group_by(Organization.id, Organization.name)
            .order_by(desc("revenue"))
            .limit(10)
            .all()
        )

        industry_comparison = [
            {
                "id": org_id,
                "name": name,
                "revenue": float(revenue or 0),
                "profit": float(profit or 0),
                "employees": int(employees or 0) if employees else None,
                "avg_salary": float(avg_salary or 0) if avg_salary else None,
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
            "industry_comparison": industry_comparison,
        },
    )


@router.get("/{organization_id}/edit", response_class=HTMLResponse)
async def edit_organization_page(
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
        "organization_edit_full.html",
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


@router.post("/{organization_id}/edit-full")
async def update_organization_full(
    request: Request, organization_id: int, db: Session = Depends(get_db)
):
    org = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    try:
        data = await request.json()

        general = data.get("general", {})
        for key, value in general.items():
            if hasattr(org, key):
                setattr(org, key, value)

        if "metrics" in data:
            db.query(OrganizationMetrics).filter(
                OrganizationMetrics.organization_id == organization_id
            ).delete()

            for metric_data in data["metrics"]:
                if metric_data.get("year"):
                    metric = OrganizationMetrics(
                        organization_id=organization_id,
                        year=int(metric_data["year"]),
                        revenue=(
                            float(metric_data["revenue"])
                            if metric_data.get("revenue")
                            else None
                        ),
                        profit=(
                            float(metric_data["profit"])
                            if metric_data.get("profit")
                            else None
                        ),
                        total_employees=(
                            int(metric_data["total_employees"])
                            if metric_data.get("total_employees")
                            else None
                        ),
                        moscow_employees=(
                            int(metric_data["moscow_employees"])
                            if metric_data.get("moscow_employees")
                            else None
                        ),
                        total_fot=(
                            float(metric_data["total_fot"])
                            if metric_data.get("total_fot")
                            else None
                        ),
                        moscow_fot=(
                            float(metric_data["moscow_fot"])
                            if metric_data.get("moscow_fot")
                            else None
                        ),
                        avg_salary_total=(
                            float(metric_data["avg_salary_total"])
                            if metric_data.get("avg_salary_total")
                            else None
                        ),
                        avg_salary_moscow=(
                            float(metric_data["avg_salary_moscow"])
                            if metric_data.get("avg_salary_moscow")
                            else None
                        ),
                        investments=(
                            float(metric_data["investments"])
                            if metric_data.get("investments")
                            else None
                        ),
                        export_volume=(
                            float(metric_data["export_volume"])
                            if metric_data.get("export_volume")
                            else None
                        ),
                    )
                    db.add(metric)

        if "taxes" in data:
            db.query(OrganizationTaxes).filter(
                OrganizationTaxes.organization_id == organization_id
            ).delete()

            for tax_data in data["taxes"]:
                if tax_data.get("year"):
                    tax = OrganizationTaxes(
                        organization_id=organization_id,
                        year=int(tax_data["year"]),
                        total_taxes_moscow=(
                            float(tax_data["total_taxes_moscow"])
                            if tax_data.get("total_taxes_moscow")
                            else None
                        ),
                        profit_tax=(
                            float(tax_data["profit_tax"])
                            if tax_data.get("profit_tax")
                            else None
                        ),
                        property_tax=(
                            float(tax_data["property_tax"])
                            if tax_data.get("property_tax")
                            else None
                        ),
                        land_tax=(
                            float(tax_data["land_tax"])
                            if tax_data.get("land_tax")
                            else None
                        ),
                        ndfl=(
                            float(tax_data["ndfl"])
                            if tax_data.get("ndfl")
                            else None
                        ),
                        transport_tax=(
                            float(tax_data["transport_tax"])
                            if tax_data.get("transport_tax")
                            else None
                        ),
                        other_taxes=(
                            float(tax_data["other_taxes"])
                            if tax_data.get("other_taxes")
                            else None
                        ),
                        excise=(
                            float(tax_data["excise"])
                            if tax_data.get("excise")
                            else None
                        ),
                    )
                    db.add(tax)

        if "assets" in data:
            db.query(OrganizationAssets).filter(
                OrganizationAssets.organization_id == organization_id
            ).delete()

            for asset_data in data["assets"]:
                asset = OrganizationAssets(
                    organization_id=organization_id,
                    cadastral_number_land=asset_data.get(
                        "cadastral_number_land"
                    ),
                    land_area=(
                        float(asset_data["land_area"])
                        if asset_data.get("land_area")
                        else None
                    ),
                    land_usage=asset_data.get("land_usage"),
                    land_ownership_type=asset_data.get("land_ownership_type"),
                    land_owner=asset_data.get("land_owner"),
                    cadastral_number_building=asset_data.get(
                        "cadastral_number_building"
                    ),
                    building_area=(
                        float(asset_data["building_area"])
                        if asset_data.get("building_area")
                        else None
                    ),
                    building_usage=asset_data.get("building_usage"),
                    building_type=asset_data.get("building_type"),
                    building_purpose=asset_data.get("building_purpose"),
                    building_ownership_type=asset_data.get(
                        "building_ownership_type"
                    ),
                    building_owner=asset_data.get("building_owner"),
                    production_area=(
                        float(asset_data["production_area"])
                        if asset_data.get("production_area")
                        else None
                    ),
                    property_summary=asset_data.get("property_summary"),
                )
                db.add(asset)

        if "products" in data:
            db.query(OrganizationProducts).filter(
                OrganizationProducts.organization_id == organization_id
            ).delete()

            for product_data in data["products"]:
                product = OrganizationProducts(
                    organization_id=organization_id,
                    product_name=product_data.get("product_name"),
                    standardized_product=product_data.get(
                        "standardized_product"
                    ),
                    okpd2_codes=product_data.get("okpd2_codes"),
                    product_types=product_data.get("product_types"),
                    product_catalog=product_data.get("product_catalog"),
                    has_government_orders=product_data.get(
                        "has_government_orders", False
                    ),
                    capacity_usage=(
                        float(product_data["capacity_usage"])
                        if product_data.get("capacity_usage")
                        else None
                    ),
                    has_export=product_data.get("has_export", False),
                    export_volume_last_year=(
                        float(product_data["export_volume_last_year"])
                        if product_data.get("export_volume_last_year")
                        else None
                    ),
                    export_countries=product_data.get("export_countries"),
                    tnved_code=product_data.get("tnved_code"),
                )
                db.add(product)

        if "meta" in data:
            meta_data = data["meta"]
            meta = (
                db.query(OrganizationMeta)
                .filter(OrganizationMeta.organization_id == organization_id)
                .first()
            )

            if meta:
                for key, value in meta_data.items():
                    if hasattr(meta, key):
                        setattr(meta, key, value)
            else:
                meta = OrganizationMeta(
                    organization_id=organization_id,
                    industry_spark=meta_data.get("industry_spark"),
                    industry_directory=meta_data.get("industry_directory"),
                    presentation_links=meta_data.get("presentation_links"),
                    registry_development=meta_data.get("registry_development"),
                    other_notes=meta_data.get("other_notes"),
                )
                db.add(meta)

        db.commit()
        logger.info(
            "organization_fully_updated", organization_id=organization_id
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": "Все данные организации успешно обновлены",
                "organization_id": organization_id,
            }
        )

    except Exception as e:
        db.rollback()
        logger.error(
            "organization_full_update_failed",
            organization_id=organization_id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{organization_id}/update-from-fns")
async def update_organization_from_fns(
    organization_id: int, db: Session = Depends(get_db)
):
    org = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org.inn:
        raise HTTPException(status_code=400, detail="Organization has no INN")

    try:
        fns_enabled = getattr(settings.get("fns_api", {}), "enabled", False)
        if not fns_enabled:
            raise HTTPException(status_code=503, detail="FNS API is disabled")

        fns_config = settings.get("fns_api", {})
        api_key = getattr(fns_config, "api_key", None)
        timeout = getattr(fns_config, "timeout", 30)

        if not api_key:
            raise HTTPException(
                status_code=503, detail="FNS API key not configured"
            )

        fns_service = get_fns_service(api_key=api_key, timeout=timeout)

        logger.info(
            "fetching_fns_data", organization_id=organization_id, inn=org.inn
        )
        fns_data = await fns_service.get_organization_by_inn(org.inn)

        if not fns_data:
            raise HTTPException(
                status_code=404,
                detail="Organization not found in FNS database",
            )

        updated_fields = []

        field_mapping = {
            "name": "name",
            "full_name": "full_name",
            "legal_address": "legal_address",
            "status_final": "status",
            "main_okved": "main_okved",
            "main_okved_name": "main_okved_name",
            "head_name": "head_name",
            "registration_date": "registration_date",
        }

        for org_field, fns_field in field_mapping.items():
            if fns_field in fns_data and fns_data[fns_field]:
                if not hasattr(org, org_field):
                    continue

                old_value = getattr(org, org_field, None)
                new_value = fns_data[fns_field]

                if old_value != new_value:
                    setattr(org, org_field, new_value)
                    updated_fields.append(org_field)

        org.updated_at = datetime.now()

        db.commit()
        logger.info(
            "organization_updated_from_fns",
            organization_id=organization_id,
            updated_fields=updated_fields,
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": f"Данные обновлены из ФНС. Обновлено полей: {len(updated_fields)}",
                "organization_id": organization_id,
                "updated_fields": updated_fields,
                "inn": org.inn,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "fns_update_failed", organization_id=organization_id, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update from FNS: {str(e)}"
        )


@router.post("/{organization_id}/import-financials")
async def import_financials_from_fns(
    organization_id: int, db: Session = Depends(get_db)
):
    org = (
        db.query(Organization)
        .filter(Organization.id == organization_id)
        .first()
    )

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not org.inn:
        raise HTTPException(status_code=400, detail="Organization has no INN")

    if len(org.inn) != 10:
        raise HTTPException(
            status_code=400,
            detail="Financial statements are only available for legal entities (ЮЛ)",
        )

    try:
        fns_enabled = getattr(settings.get("fns_api", {}), "enabled", False)
        if not fns_enabled:
            raise HTTPException(status_code=503, detail="FNS API is disabled")

        fns_config = settings.get("fns_api", {})
        api_key = getattr(fns_config, "api_key", None)
        timeout = getattr(fns_config, "timeout", 30)

        if not api_key:
            raise HTTPException(
                status_code=503, detail="FNS API key not configured"
            )

        fns_service = get_fns_service(api_key=api_key, timeout=timeout)

        logger.info(
            "fetching_fns_financials",
            organization_id=organization_id,
            inn=org.inn,
        )
        financial_data = await fns_service.get_financial_statements(org.inn)

        if not financial_data:
            raise HTTPException(
                status_code=404,
                detail="Financial statements not found in FNS database",
            )

        imported_years = []
        updated_years = []

        for year_str, year_data in financial_data.items():
            try:
                year = int(year_str)
            except ValueError:
                continue

            existing_metric = (
                db.query(OrganizationMetrics)
                .filter(
                    OrganizationMetrics.organization_id == organization_id,
                    OrganizationMetrics.year == year,
                )
                .first()
            )

            revenue = year_data.get("2110")
            profit = year_data.get("2400")

            if existing_metric:
                if revenue is not None:
                    existing_metric.revenue = float(revenue) * 1000
                if profit is not None:
                    existing_metric.profit = float(profit) * 1000
                updated_years.append(year)
            else:
                new_metric = OrganizationMetrics(
                    organization_id=organization_id,
                    year=year,
                    revenue=(
                        float(revenue) * 1000 if revenue is not None else None
                    ),
                    profit=(
                        float(profit) * 1000 if profit is not None else None
                    ),
                )
                db.add(new_metric)
                imported_years.append(year)

        db.commit()
        logger.info(
            "financials_imported_from_fns",
            organization_id=organization_id,
            imported_years=imported_years,
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": "Бухгалтерская отчётность импортирована из ФНС",
                "organization_id": organization_id,
                "imported_years": sorted(imported_years),
                "updated_years": sorted(updated_years),
                "total_years": len(imported_years) + len(updated_years),
                "inn": org.inn,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "financials_import_failed",
            organization_id=organization_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import financials from FNS: {str(e)}",
        )
