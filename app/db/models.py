"""Database models for the application."""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Index, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Organization(Base):
    """Organization model - основная информация о компании."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False, index=True)
    full_name = Column(String(1000))
    status_spark = Column(String(200))
    status_internal = Column(String(200))
    status_final = Column(String(200))
    date_added = Column(DateTime)
    legal_address = Column(String(1000))
    production_address = Column(String(1000))
    additional_address = Column(String(1000))
    main_industry = Column(String(200))
    main_subindustry = Column(String(200))
    extra_industry = Column(String(200))
    extra_subindustry = Column(String(200))
    main_okved = Column(String(100))
    main_okved_name = Column(String(200))
    prod_okved = Column(String(100))
    prod_okved_name = Column(String(200))
    company_info = Column(Text)
    company_size = Column(String(100))
    company_size_2022 = Column(String(100))
    size_by_employees = Column(String(100))
    size_by_employees_2022 = Column(String(100))
    size_by_revenue = Column(String(100))
    size_by_revenue_2022 = Column(String(100))
    registration_date = Column(DateTime)
    head_name = Column(String(200))
    parent_org_name = Column(String(500))
    parent_org_inn = Column(String(12))
    parent_relation_type = Column(String(200))
    head_contacts = Column(String(500))
    head_email = Column(String(200))
    employee_contact = Column(String(500))
    phone = Column(String(100))
    emergency_contact = Column(String(500))
    website = Column(String(300))
    email = Column(String(200))
    support_data = Column(Text)
    special_status = Column(String(200))
    site_final = Column(String(200))
    got_moscow_support = Column(Boolean, default=False)
    is_system_critical = Column(Boolean, default=False)
    msp_status = Column(String(100))
    coordinates_lat = Column(Float)
    coordinates_lon = Column(Float)
    legal_address_coords = Column(String(200))  # Координаты юридического адреса
    production_address_coords = Column(String(200))  # Координаты адреса производства
    additional_address_coords = Column(String(200))  # Координаты адреса дополнительной площадки
    district = Column(String(200))
    region = Column(String(200))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    metrics = relationship("OrganizationMetrics", back_populates="organization", cascade="all, delete-orphan")
    taxes = relationship("OrganizationTaxes", back_populates="organization", cascade="all, delete-orphan")
    assets = relationship("OrganizationAssets", back_populates="organization", cascade="all, delete-orphan")
    products = relationship("OrganizationProducts", back_populates="organization", cascade="all, delete-orphan")
    meta = relationship("OrganizationMeta", back_populates="organization", cascade="all, delete-orphan")

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
    profit = Column(Float)
    total_employees = Column(Integer)
    moscow_employees = Column(Integer)
    total_fot = Column(Float)
    moscow_fot = Column(Float)
    avg_salary_total = Column(Float)
    avg_salary_moscow = Column(Float)
    investments = Column(Float)
    export_volume = Column(Float)  # Объем экспорта

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


class OrganizationTaxes(Base):
    __tablename__ = "organization_taxes"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False, index=True)

    total_taxes_moscow = Column(Float)
    profit_tax = Column(Float)
    property_tax = Column(Float)
    land_tax = Column(Float)
    ndfl = Column(Float)
    transport_tax = Column(Float)
    other_taxes = Column(Float)
    excise = Column(Float)

    organization = relationship("Organization", back_populates="taxes")


class OrganizationAssets(Base):
    __tablename__ = "organization_assets"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    cadastral_number_land = Column(String(200))
    land_area = Column(Float)
    land_usage = Column(String(200))
    land_ownership_type = Column(String(200))
    land_owner = Column(String(500))

    cadastral_number_building = Column(String(200))
    building_area = Column(Float)
    building_usage = Column(String(200))
    building_type = Column(String(200))
    building_purpose = Column(String(200))
    building_ownership_type = Column(String(200))
    building_owner = Column(String(500))
    production_area = Column(Float)
    property_summary = Column(Text)

    organization = relationship("Organization", back_populates="assets")


class OrganizationProducts(Base):
    __tablename__ = "organization_products"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    product_name = Column(String(500))
    standardized_product = Column(String(500))
    okpd2_codes = Column(String(500))
    product_types = Column(String(500))
    product_catalog = Column(String(500))
    has_government_orders = Column(Boolean, default=False)
    capacity_usage = Column(String(200))
    has_export = Column(Boolean, default=False)
    export_volume_last_year = Column(Float)
    export_countries = Column(String(1000))
    tnved_code = Column(String(100))

    organization = relationship("Organization", back_populates="products")


class OrganizationMeta(Base):
    __tablename__ = "organization_meta"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    industry_spark = Column(String(500))
    industry_directory = Column(String(500))
    presentation_links = Column(String(1000))
    registry_development = Column(Text)
    other_notes = Column(Text)

    organization = relationship("Organization", back_populates="meta")
