"""Test script to upload Excel file directly."""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url
from app.services.excel_processor_v2 import process_excel_file

# Get the Excel file path
excel_file = Path("Тип данных от организаций.xlsx")

if not excel_file.exists():
    print(f"ERROR: Excel file not found: {excel_file}")
    print(f"Current directory: {Path.cwd()}")
    exit(1)

print(f"OK: Excel file found: {excel_file}")
print(f"File size: {excel_file.stat().st_size / 1024:.2f} KB")

# Create database session
database_url = get_database_url()
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    print("\nProcessing Excel file...")
    result = process_excel_file(excel_file, db)
    
    print("\nProcessing completed successfully!")
    print(f"\nStatistics:")
    print(f"  * New organizations: {result['organizations_new']}")
    print(f"  * Updated organizations: {result['organizations_updated']}")
    print(f"  * Total rows processed: {result['rows_processed']}")
    print(f"  * Skipped rows: {result['rows_skipped']}")
    print(f"  * Errors: {len(result['errors'])}")
    
    if result['errors']:
        print("\nErrors during processing:")
        for error in result['errors'][:10]:  # Show first 10 errors
            print(f"  * Row {error['row']}: {error['inn']} - {error['name']}")
            print(f"    Error: {error['error']}")
    
except Exception as e:
    print(f"\nERROR during processing: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
