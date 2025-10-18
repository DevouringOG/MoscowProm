"""Check exact column indices for district and region."""
import openpyxl
from pathlib import Path

excel_file = Path("Тип данных от организаций.xlsx")
workbook = openpyxl.load_workbook(excel_file, data_only=True)
sheet = workbook.active

# Get headers
headers = []
for cell in sheet[1]:
    headers.append(cell.value)

print(f"Total columns: {len(headers)}\n")

# Find coordinate-related and district/region columns
search_terms = [
    'Координаты юридического адреса',
    'Координаты адреса производства',
    'Координаты адреса дополнительной площадки',
    'Координаты (широта)',
    'Координаты (долгота)',
    'Округ',
    'Район'
]

print("Looking for columns:")
for term in search_terms:
    for i, h in enumerate(headers):
        if h and term.lower() in str(h).lower():
            print(f"  [{i:3d}] '{h}'")
            break
    else:
        print(f"  NOT FOUND: '{term}'")

# Show last 15 columns
print(f"\nLast 15 columns:")
for i in range(len(headers) - 15, len(headers)):
    h = headers[i] if i < len(headers) else 'N/A'
    print(f"  [{i:3d}] '{h}'")

# Check sample data row
row = list(sheet.iter_rows(min_row=2, max_row=2, values_only=True))[0]
print(f"\nSample data from last columns (row 2):")
for i in range(len(headers) - 15, len(headers)):
    val = row[i] if i < len(row) else 'N/A'
    print(f"  [{i:3d}] = '{val}'")
