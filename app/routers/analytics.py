from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from app.db import get_db
from app.db.models import Organization, OrganizationMetrics, OrganizationTaxes
from app.dependencies.templates import templates
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/analytics", response_class=HTMLResponse)
async def analytics(
    request: Request,
    db: Session = Depends(get_db),
    industries: list[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    company_sizes: list[str] = Query(None),
    districts: list[str] = Query(None),
):
    try:
        org_filter = []
        metrics_filter = []

        if industries:
            org_filter.append(Organization.main_industry.in_(industries))
        if company_sizes:
            org_filter.append(Organization.company_size.in_(company_sizes))
        if districts:
            org_filter.append(Organization.district.in_(districts))

        if year_from:
            metrics_filter.append(OrganizationMetrics.year >= year_from)
        if year_to:
            metrics_filter.append(OrganizationMetrics.year <= year_to)

        all_industries = (
            db.query(func.distinct(Organization.main_industry))
            .filter(Organization.main_industry.isnot(None))
            .order_by(Organization.main_industry)
            .all()
        )
        all_industries = [ind[0] for ind in all_industries if ind[0]]

        all_years = (
            db.query(func.distinct(OrganizationMetrics.year))
            .order_by(OrganizationMetrics.year)
            .all()
        )
        all_years = [year[0] for year in all_years if year[0]]

        all_company_sizes = (
            db.query(func.distinct(Organization.company_size))
            .filter(Organization.company_size.isnot(None))
            .order_by(Organization.company_size)
            .all()
        )
        all_company_sizes = [size[0] for size in all_company_sizes if size[0]]

        all_districts = (
            db.query(func.distinct(Organization.district))
            .filter(Organization.district.isnot(None))
            .order_by(Organization.district)
            .all()
        )
        all_districts = [dist[0] for dist in all_districts if dist[0]]

        if not year_from and all_years:
            year_from = min(all_years)
        if not year_to and all_years:
            year_to = max(all_years)

        latest_year = year_to or datetime.now().year

        org_query = db.query(Organization)
        if org_filter:
            org_query = org_query.filter(and_(*org_filter))
        total_organizations = org_query.count()

        revenue_query = (
            db.query(func.sum(OrganizationMetrics.revenue))
            .join(Organization)
            .filter(OrganizationMetrics.year == latest_year)
        )
        if org_filter:
            revenue_query = revenue_query.filter(and_(*org_filter))
        total_revenue = revenue_query.scalar() or 0

        prev_revenue_query = (
            db.query(func.sum(OrganizationMetrics.revenue))
            .join(Organization)
            .filter(OrganizationMetrics.year == latest_year - 1)
        )
        if org_filter:
            prev_revenue_query = prev_revenue_query.filter(and_(*org_filter))
        prev_year_revenue = prev_revenue_query.scalar() or 0

        revenue_change = 0
        if prev_year_revenue > 0:
            revenue_change = (
                (total_revenue - prev_year_revenue) / prev_year_revenue
            ) * 100

        employees_query = (
            db.query(func.sum(OrganizationMetrics.total_employees))
            .join(Organization)
            .filter(OrganizationMetrics.year == latest_year)
        )
        if org_filter:
            employees_query = employees_query.filter(and_(*org_filter))
        total_employees = employees_query.scalar() or 0

        investments_query = (
            db.query(func.sum(OrganizationMetrics.investments))
            .join(Organization)
            .filter(OrganizationMetrics.year == latest_year)
        )
        if org_filter:
            investments_query = investments_query.filter(and_(*org_filter))
        total_investments = investments_query.scalar() or 0

        export_query = (
            db.query(func.sum(OrganizationMetrics.export_volume))
            .join(Organization)
            .filter(OrganizationMetrics.year == latest_year)
        )
        if org_filter:
            export_query = export_query.filter(and_(*org_filter))
        total_export = export_query.scalar() or 0

        taxes_query = (
            db.query(func.sum(OrganizationTaxes.total_taxes_moscow))
            .join(Organization)
            .filter(OrganizationTaxes.year == latest_year)
        )
        if org_filter:
            taxes_query = taxes_query.filter(and_(*org_filter))
        total_taxes = taxes_query.scalar() or 0

        avg_salary_query = (
            db.query(func.avg(OrganizationMetrics.avg_salary_total))
            .join(Organization)
            .filter(OrganizationMetrics.year == latest_year)
        )
        if org_filter:
            avg_salary_query = avg_salary_query.filter(and_(*org_filter))
        avg_salary = avg_salary_query.scalar() or 0

        revenue_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.revenue).label("revenue"),
        ).join(Organization)
        if org_filter:
            revenue_by_year_query = revenue_by_year_query.filter(
                and_(*org_filter)
            )
        if metrics_filter:
            revenue_by_year_query = revenue_by_year_query.filter(
                and_(*metrics_filter)
            )
        revenue_by_year = (
            revenue_by_year_query.group_by(OrganizationMetrics.year)
            .order_by(OrganizationMetrics.year)
            .all()
        )

        revenue_by_year_data = [
            {"year": year, "revenue": float(revenue or 0)}
            for year, revenue in revenue_by_year
        ]

        employees_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.total_employees).label("employees"),
        ).join(Organization)
        if org_filter:
            employees_by_year_query = employees_by_year_query.filter(
                and_(*org_filter)
            )
        if metrics_filter:
            employees_by_year_query = employees_by_year_query.filter(
                and_(*metrics_filter)
            )
        employees_by_year = (
            employees_by_year_query.group_by(OrganizationMetrics.year)
            .order_by(OrganizationMetrics.year)
            .all()
        )

        employees_by_year_data = [
            {"year": year, "employees": int(employees or 0)}
            for year, employees in employees_by_year
        ]

        investments_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.investments).label("investments"),
        ).join(Organization)
        if org_filter:
            investments_by_year_query = investments_by_year_query.filter(
                and_(*org_filter)
            )
        if metrics_filter:
            investments_by_year_query = investments_by_year_query.filter(
                and_(*metrics_filter)
            )
        investments_by_year = (
            investments_by_year_query.group_by(OrganizationMetrics.year)
            .order_by(OrganizationMetrics.year)
            .all()
        )

        investments_by_year_data = [
            {"year": year, "investments": float(investments or 0)}
            for year, investments in investments_by_year
        ]

        export_by_year_query = db.query(
            OrganizationMetrics.year,
            func.sum(OrganizationMetrics.export_volume).label("export_volume"),
        ).join(Organization)
        if org_filter:
            export_by_year_query = export_by_year_query.filter(
                and_(*org_filter)
            )
        if metrics_filter:
            export_by_year_query = export_by_year_query.filter(
                and_(*metrics_filter)
            )
        export_by_year = (
            export_by_year_query.group_by(OrganizationMetrics.year)
            .order_by(OrganizationMetrics.year)
            .all()
        )

        export_by_year_data = [
            {"year": year, "export": float(export_volume or 0)}
            for year, export_volume in export_by_year
        ]

        taxes_by_year_query = db.query(
            OrganizationTaxes.year,
            func.sum(OrganizationTaxes.total_taxes_moscow).label("taxes"),
        ).join(Organization)
        if org_filter:
            taxes_by_year_query = taxes_by_year_query.filter(and_(*org_filter))
        if metrics_filter:
            taxes_by_year_query = taxes_by_year_query.filter(
                and_(*metrics_filter)
            )
        taxes_by_year = (
            taxes_by_year_query.group_by(OrganizationTaxes.year)
            .order_by(OrganizationTaxes.year)
            .all()
        )

        taxes_by_year_data = [
            {"year": year, "taxes": float(taxes or 0)}
            for year, taxes in taxes_by_year
        ]

        salary_by_year_query = db.query(
            OrganizationMetrics.year,
            func.avg(OrganizationMetrics.avg_salary_total).label("avg_salary"),
        ).join(Organization)
        if org_filter:
            salary_by_year_query = salary_by_year_query.filter(
                and_(*org_filter)
            )
        if metrics_filter:
            salary_by_year_query = salary_by_year_query.filter(
                and_(*metrics_filter)
            )
        salary_by_year = (
            salary_by_year_query.group_by(OrganizationMetrics.year)
            .order_by(OrganizationMetrics.year)
            .all()
        )

        salary_by_year_data = [
            {"year": year, "salary": float(avg_salary or 0)}
            for year, avg_salary in salary_by_year
        ]

        revenue_by_industry_query = (
            db.query(
                Organization.main_industry,
                func.sum(OrganizationMetrics.revenue).label("revenue"),
            )
            .join(OrganizationMetrics)
            .filter(
                Organization.main_industry.isnot(None),
                OrganizationMetrics.year == latest_year,
            )
        )
        if org_filter:
            revenue_by_industry_query = revenue_by_industry_query.filter(
                and_(*org_filter)
            )
        revenue_by_industry = (
            revenue_by_industry_query.group_by(Organization.main_industry)
            .order_by(desc("revenue"))
            .limit(10)
            .all()
        )

        revenue_by_industry_data = [
            {"industry": ind or "Не указано", "revenue": float(rev or 0)}
            for ind, rev in revenue_by_industry
        ]

        top_orgs_query = db.query(
            Organization.id,
            Organization.name,
            Organization.main_industry,
            func.sum(OrganizationMetrics.revenue).label("revenue"),
            func.sum(OrganizationMetrics.total_employees).label("employees"),
            func.avg(OrganizationMetrics.avg_salary_total).label("avg_salary"),
        ).join(OrganizationMetrics)
        if org_filter:
            top_orgs_query = top_orgs_query.filter(and_(*org_filter))
        if metrics_filter:
            top_orgs_query = top_orgs_query.filter(and_(*metrics_filter))
        top_orgs = (
            top_orgs_query.group_by(
                Organization.id, Organization.name, Organization.main_industry
            )
            .order_by(desc("revenue"))
            .limit(10)
            .all()
        )

        top_organizations = [
            {
                "id": org_id,
                "name": name,
                "main_industry": industry or "Не указано",
                "revenue": float(revenue or 0),
                "employees": int(employees or 0) if employees else 0,
                "avg_salary": float(avg_salary or 0) if avg_salary else 0,
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
                "all_industries": all_industries,
                "all_years": all_years,
                "all_company_sizes": all_company_sizes,
                "all_districts": all_districts,
                "selected_industries": industries or [],
                "selected_year_from": year_from,
                "selected_year_to": year_to,
                "selected_company_sizes": company_sizes or [],
                "selected_districts": districts or [],
            },
        )

    except Exception as e:
        logger.error("analytics_page_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
