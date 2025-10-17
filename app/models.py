"""Database models for the application."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Organization(Base):
    """Organization model - основная информация о компании."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    inn = Column(String(12), unique=True, nullable=False, index=True)
    address = Column(String(1000))
    industry = Column(String(200), index=True)
    sub_industry = Column(String(200))
    status = Column(String(100))  # МСП/системообразующее
    email = Column(String(200))
    phone = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    metrics = relationship("OrganizationMetrics", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, inn={self.inn})>"


class OrganizationMetrics(Base):
    """Organization metrics - временные ряды метрик по годам."""

    __tablename__ = "organization_metrics"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False, index=True)

    # Financial metrics
    revenue = Column(Float)  # Выручка
    export_volume = Column(Float)  # Объем экспорта
    investments = Column(Float)  # Инвестиции
    payroll_fund = Column(Float)  # Фонд оплаты труда
    average_salary = Column(Float)  # Средняя зарплата

    # Employment metrics
    employees_count = Column(Integer)  # Количество сотрудников

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="metrics")

    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_org_metrics_org_year", "organization_id", "year"),
    )

    def __repr__(self):
        return f"<OrganizationMetrics(org_id={self.organization_id}, year={self.year})>"
