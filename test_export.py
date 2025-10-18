"""Test script for Excel export functionality."""
import sys
print("Starting test script...", file=sys.stderr)

try:
    from sqlalchemy.orm import Session
    from app.db import engine, SessionLocal
    from app.db.models import Organization
    from app.services.excel_exporter import export_organizations_to_excel
    print("Imports successful", file=sys.stderr)
except Exception as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

def test_export():
    """Test the export functionality."""
    print("Creating database session...", file=sys.stderr)
    db = SessionLocal()
    
    try:
        # Get first 5 organizations for testing
        organizations = db.query(Organization).limit(5).all()
        
        if not organizations:
            print("❌ No organizations found in database")
            return False
        
        print(f"✅ Found {len(organizations)} organizations")
        
        # Test export
        excel_file = export_organizations_to_excel(organizations, db)
        
        if excel_file:
            print("✅ Excel file generated successfully")
            print(f"   File size: {len(excel_file.getvalue())} bytes")
            
            # Save test file
            with open("test_export.xlsx", "wb") as f:
                f.write(excel_file.getvalue())
            print("✅ Test file saved as test_export.xlsx")
            
            return True
        else:
            print("❌ Failed to generate Excel file")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing Excel export functionality...")
    print("-" * 50)
    success = test_export()
    print("-" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
