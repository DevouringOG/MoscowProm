"""Check what data was actually saved to database."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from app.db.models import Organization, OrganizationMetrics, OrganizationTaxes

# Create database session
database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Count organizations
    org_count = db.query(Organization).count()
    print(f"Total organizations: {org_count}")
    
    # Get first organization
    org = db.query(Organization).first()
    if org:
        print(f"\nFirst organization:")
        print(f"  INN: {org.inn}")
        print(f"  Name: {org.name}")
        print(f"  Main industry: {org.main_industry}")
        print(f"  Phone: {org.phone}")
        print(f"  Email: {org.email}")
        print(f"  Website: {org.website}")
        
        # Check metrics
        metrics = db.query(OrganizationMetrics).filter(
            OrganizationMetrics.organization_id == org.id
        ).all()
        print(f"\n  Metrics records: {len(metrics)}")
        if metrics:
            for m in metrics[:3]:  # Show first 3 years
                print(f"    {m.year}: Revenue={m.revenue}, Profit={m.profit}, Employees={m.total_employees}, FOT={m.total_fot}")
        
        # Check taxes
        taxes = db.query(OrganizationTaxes).filter(
            OrganizationTaxes.organization_id == org.id
        ).all()
        print(f"\n  Tax records: {len(taxes)}")
        if taxes:
            for t in taxes[:3]:  # Show first 3 years
                print(f"    {t.year}: Total={t.total_taxes_moscow}, Profit tax={t.profit_tax}, NDFL={t.ndfl}, Excise={t.excise}")
    
    # Check specific INN from user's example
    svetotekhnika = db.query(Organization).filter(Organization.inn == '7706901234').first()
    if svetotekhnika:
        print(f"\n\nOrganization from user example (INN=7706901234):")
        print(f"  Name: {svetotekhnika.name}")
        
        # Check metrics for 2017
        metrics_2017 = db.query(OrganizationMetrics).filter(
            OrganizationMetrics.organization_id == svetotekhnika.id,
            OrganizationMetrics.year == 2017
        ).first()
        
        if metrics_2017:
            print(f"\n  2017 Metrics:")
            print(f"    Revenue: {metrics_2017.revenue} (expected: 645670)")
            print(f"    Profit: {metrics_2017.profit} (expected: 67890)")
            print(f"    Total employees: {metrics_2017.total_employees} (expected: 223)")
            print(f"    Moscow employees: {metrics_2017.moscow_employees} (expected: 223)")
            print(f"    Total FOT: {metrics_2017.total_fot} (expected: 156780)")
            print(f"    Moscow FOT: {metrics_2017.moscow_fot} (expected: 156780)")
            print(f"    Avg salary total: {metrics_2017.avg_salary_total} (expected: 58.6)")
            print(f"    Avg salary Moscow: {metrics_2017.avg_salary_moscow} (expected: 58.6)")
        
        # Check taxes for 2017
        taxes_2017 = db.query(OrganizationTaxes).filter(
            OrganizationTaxes.organization_id == svetotekhnika.id,
            OrganizationTaxes.year == 2017
        ).first()
        
        if taxes_2017:
            print(f"\n  2017 Taxes:")
            print(f"    Total taxes Moscow: {taxes_2017.total_taxes_moscow} (expected: 71230)")
            print(f"    Profit tax: {taxes_2017.profit_tax} (expected: 13578)")
            print(f"    Property tax: {taxes_2017.property_tax} (expected: 4890)")
            print(f"    Land tax: {taxes_2017.land_tax} (expected: 2450)")
            print(f"    NDFL: {taxes_2017.ndfl} (expected: 48670)")
            print(f"    Transport tax: {taxes_2017.transport_tax} (expected: 289)")
            print(f"    Other taxes: {taxes_2017.other_taxes} (expected: 644)")
            print(f"    Excise: {taxes_2017.excise} (expected: 0)")
        
        # Check 2023 data
        metrics_2023 = db.query(OrganizationMetrics).filter(
            OrganizationMetrics.organization_id == svetotekhnika.id,
            OrganizationMetrics.year == 2023
        ).first()
        
        if metrics_2023:
            print(f"\n  2023 Metrics:")
            print(f"    Revenue: {metrics_2023.revenue} (expected: 1334560)")
            print(f"    Investments: {metrics_2023.investments} (expected: 94560)")
            print(f"    Export volume: {metrics_2023.export_volume} (expected: 159670)")

finally:
    db.close()
