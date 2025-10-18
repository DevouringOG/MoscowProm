"""Test upload endpoint and check JSON response."""
import json
from pathlib import Path
from app.db import get_db
from app.services.excel_processor_v2 import process_excel_file

# Get Excel file
excel_file = Path("Тип данных от организаций.xlsx")

if not excel_file.exists():
    print(f"❌ ERROR: Excel file not found: {excel_file}")
    exit(1)

print(f"✅ Excel file found: {excel_file.name}")
print(f"File size: {excel_file.stat().st_size / 1024:.2f} KB")

# Process file
db = next(get_db())
result = process_excel_file(excel_file, db)

# Print JSON response
print("\n" + "="*80)
print("JSON Response:")
print("="*80)
print(json.dumps(result, indent=2, ensure_ascii=False))
print("="*80)

# Check required fields
required_fields = ['organizations_count', 'organizations_new', 'organizations_updated', 'organizations_details']
missing = [f for f in required_fields if f not in result]

if missing:
    print(f"\n❌ Missing fields: {missing}")
else:
    print(f"\n✅ All required fields present")
    print(f"   - organizations_count: {result['organizations_count']}")
    print(f"   - organizations_new: {result['organizations_new']}")
    print(f"   - organizations_updated: {result['organizations_updated']}")
    print(f"   - organizations_details: {len(result['organizations_details'])} items")
    
    if result['organizations_details']:
        print(f"\nFirst organization:")
        print(json.dumps(result['organizations_details'][0], indent=2, ensure_ascii=False))
