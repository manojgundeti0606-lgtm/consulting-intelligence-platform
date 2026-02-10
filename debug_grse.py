"""Debug GRSE table row structure"""
import requests
from bs4 import BeautifulSoup

url = 'https://eprocuregrse.co.in/nicgep/app?page=FrontEndLatestActiveTenders&service=page'
r = requests.get(url, timeout=30)
soup = BeautifulSoup(r.text, 'html.parser')

# Find list_table
table = soup.find('table', class_='list_table')
print(f"Found list_table: {table is not None}")

if table:
    rows = table.find_all('tr')
    print(f"Rows: {len(rows)}")
    
    for i, row in enumerate(rows[:5]):
        cells = row.find_all(['td', 'th'])
        print(f"\nRow {i}: {len(cells)} cells")
        row_text = row.get_text()[:100].replace('\n', ' ')
        print(f"  Text: {row_text}")
        for j, cell in enumerate(cells[:6]):
            cell_text = cell.get_text(strip=True)[:50]
            print(f"    Cell {j}: {cell_text}")
