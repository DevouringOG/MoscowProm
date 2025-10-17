"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# Organization schemas
class OrganizationBase(BaseModel):
    """Base organization schema."""

    name: str = Field(..., min_length=1, max_length=500)
    inn: str = Field(..., min_length=10, max_length=12)
    address: Optional[str] = Field(None, max_length=1000)
    industry: Optional[str] = Field(None, max_length=200)
    sub_industry: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=100)

    @field_validator("inn")
    @classmethod
    def validate_inn(cls, v: str) -> str:
        """Validate INN format (10 or 12 digits)."""
        if not v.isdigit():
            raise ValueError("INN must contain only digits")
        if len(v) not in [10, 12]:
            raise ValueError("INN must be 10 or 12 digits long")
        return v


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization."""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    address: Optional[str] = Field(None, max_length=1000)
    industry: Optional[str] = Field(None, max_length=200)
    sub_industry: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=100)


class Organization(OrganizationBase):
    """Schema for organization response."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Organization Metrics schemas
class OrganizationMetricsBase(BaseModel):
    """Base organization metrics schema."""

    year: int = Field(..., ge=2000, le=2100)
    revenue: Optional[float] = Field(None, ge=0)
    export_volume: Optional[float] = Field(None, ge=0)
    investments: Optional[float] = Field(None, ge=0)
    payroll_fund: Optional[float] = Field(None, ge=0)
    average_salary: Optional[float] = Field(None, ge=0)
    employees_count: Optional[int] = Field(None, ge=0)


class OrganizationMetricsCreate(OrganizationMetricsBase):
    """Schema for creating organization metrics."""

    organization_id: int


class OrganizationMetrics(OrganizationMetricsBase):
    """Schema for organization metrics response."""

    id: int
    organization_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrganizationWithMetrics(Organization):
    """Organization with all metrics."""

    metrics: List[OrganizationMetrics] = []


# Pagination schema
class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    total: int
    page: int
    page_size: int
    items: List[Organization]


# Health check schema
class HealthCheck(BaseModel):
    """Health check response schema."""

    status: str
    database: bool
    redis: bool
    timestamp: datetime
