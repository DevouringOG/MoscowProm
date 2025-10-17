"""API routes for the application."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import crud
from app.api import schemas
from app.db import get_db
from app.redis_client import redis_client
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=schemas.HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Checks status of:
    - Database connection
    - Redis connection
    """
    db_status = False
    redis_status = False

    try:
        # Check database
        db.execute("SELECT 1")
        db_status = True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))

    try:
        # Check Redis
        redis_status = redis_client.ping()
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))

    status = "healthy" if (db_status and redis_status) else "unhealthy"

    return schemas.HealthCheck(
        status=status,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.now(),
    )


@router.get("/organizations", response_model=schemas.PaginatedResponse)
async def get_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of organizations.
    
    Args:
        page: Page number (starting from 1)
        page_size: Number of items per page
    """
    # Calculate offset
    skip = (page - 1) * page_size

    # Try to get from cache
    cache_key = f"organizations:page:{page}:size:{page_size}"
    cached = redis_client.get(cache_key)
    if cached:
        logger.info("organizations_cache_hit", page=page, page_size=page_size)
        return cached

    # Get from database
    organizations = crud.get_organizations(db, skip=skip, limit=page_size)
    total = crud.get_organizations_count(db)

    response = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [schemas.Organization.model_validate(org) for org in organizations],
    }

    # Cache the response
    redis_client.set(cache_key, response, ttl=300)  # 5 minutes cache

    logger.info("organizations_fetched", page=page, page_size=page_size, total=total)
    return response


@router.get("/organizations/{organization_id}", response_model=schemas.OrganizationWithMetrics)
async def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
):
    """
    Get organization by ID with all metrics.
    
    Args:
        organization_id: Organization ID
    """
    # Try to get from cache
    cache_key = f"organization:{organization_id}"
    cached = redis_client.get(cache_key)
    if cached:
        logger.info("organization_cache_hit", organization_id=organization_id)
        return cached

    # Get from database
    organization = crud.get_organization(db, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get metrics
    metrics = crud.get_organization_metrics(db, organization_id)

    response = schemas.OrganizationWithMetrics.model_validate(organization)
    response.metrics = [schemas.OrganizationMetrics.model_validate(m) for m in metrics]

    # Cache the response
    redis_client.set(cache_key, response, ttl=600)  # 10 minutes cache

    logger.info("organization_fetched", organization_id=organization_id)
    return response
