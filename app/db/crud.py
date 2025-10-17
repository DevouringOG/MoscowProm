"""CRUD operations for database models."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import models
from app.api import schemas


def get_organization(db: Session, organization_id: int) -> Optional[models.Organization]:
    """Get organization by ID."""
    return db.query(models.Organization).filter(models.Organization.id == organization_id).first()


def get_organization_by_inn(db: Session, inn: str) -> Optional[models.Organization]:
    """Get organization by INN."""
    return db.query(models.Organization).filter(models.Organization.inn == inn).first()


def get_organizations(
    db: Session, skip: int = 0, limit: int = 50
) -> List[models.Organization]:
    """Get list of organizations with pagination."""
    return db.query(models.Organization).offset(skip).limit(limit).all()


def get_organizations_count(db: Session) -> int:
    """Get total count of organizations."""
    return db.query(func.count(models.Organization.id)).scalar()


def create_organization(
    db: Session, organization: schemas.OrganizationCreate
) -> models.Organization:
    """Create new organization."""
    db_org = models.Organization(**organization.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


def update_organization(
    db: Session, organization_id: int, organization: schemas.OrganizationUpdate
) -> Optional[models.Organization]:
    """Update organization."""
    db_org = get_organization(db, organization_id)
    if db_org:
        for key, value in organization.model_dump(exclude_unset=True).items():
            setattr(db_org, key, value)
        db.commit()
        db.refresh(db_org)
    return db_org


def delete_organization(db: Session, organization_id: int) -> bool:
    """Delete organization."""
    db_org = get_organization(db, organization_id)
    if db_org:
        db.delete(db_org)
        db.commit()
        return True
    return False


# Organization Metrics CRUD
def create_organization_metrics(
    db: Session, metrics: schemas.OrganizationMetricsCreate
) -> models.OrganizationMetrics:
    """Create organization metrics."""
    db_metrics = models.OrganizationMetrics(**metrics.model_dump())
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def get_organization_metrics(
    db: Session, organization_id: int, year: Optional[int] = None
) -> List[models.OrganizationMetrics]:
    """Get metrics for organization, optionally filtered by year."""
    query = db.query(models.OrganizationMetrics).filter(
        models.OrganizationMetrics.organization_id == organization_id
    )
    if year:
        query = query.filter(models.OrganizationMetrics.year == year)
    return query.order_by(models.OrganizationMetrics.year).all()
