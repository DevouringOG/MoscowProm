"""Check if district and region data was loaded correctly."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from app.db.models import Organization

# Create database session
database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Get all organizations and check district/region
    orgs = db.query(Organization).all()
    
    print(f"Total organizations: {len(orgs)}\n")
    
    # Count organizations with district/region
    with_district = sum(1 for org in orgs if org.district)
    with_region = sum(1 for org in orgs if org.region)
    
    print(f"Organizations with Okrug (district): {with_district}/{len(orgs)}")
    print(f"Organizations with Raion (region): {with_region}/{len(orgs)}\n")
    
    # Show first 10 organizations
    print("First 10 organizations:")
    for i, org in enumerate(orgs[:10], 1):
        print(f"\n{i}. {org.name} (INN: {org.inn})")
        print(f"   Okrug: {org.district or 'NOT SET'}")
        print(f"   Raion: {org.region or 'NOT SET'}")
        print(f"   Coordinates: lat={org.coordinates_lat}, lon={org.coordinates_lon}")
    
    # Check specific INN from sample data
    print("\n" + "="*60)
    print("Sample organization (INN=7743125689):")
    org = db.query(Organization).filter(Organization.inn == '7743125689').first()
    if org:
        print(f"  Name: {org.name}")
        print(f"  Okrug: {org.district} (expected: YuAO)")
        print(f"  Raion: {org.region} (expected: Danilovskiy)")
        print(f"  Coordinates: lat={org.coordinates_lat}, lon={org.coordinates_lon}")
        print(f"  Legal address coords: {org.legal_address_coords}")
        print(f"  Production address coords: {org.production_address_coords}")
    
finally:
    db.close()
