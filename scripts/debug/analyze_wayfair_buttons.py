import asyncio
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add scraper to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scraper"))
from scraper import fetch_dynamic_html

async def analyze_wayfair():
    url = "https://www.wayfair.com/furniture/pdp/latitude-run-sargon-upholstered-low-profile-standard-bed-w003780954.html"
    
    print("Fetching Wayfair...")
    html = await fetch_dynamic_html(url)
    
    if not html:
        print("Failed to get HTML")
        return
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Look for ALL buttons
    all_buttons = soup.find_all('button')
    print(f"\nTotal buttons found: {len(all_buttons)}\n")
    
    # Show first 20 buttons with their attributes
    print("First 30 buttons:")
    for i, btn in enumerate(all_buttons[:30]):
        text = btn.get_text().strip()[:60]
        # Get key attributes
        data_attrs = {k: v for k, v in btn.attrs.items() if k.startswith('data-') or k in ['id', 'class', 'aria-label']}
        print(f"{i+1}. Text: '{text}'")
        if data_attrs:
            print(f"   Attrs: {data_attrs}")
        print()

asyncio.run(analyze_wayfair())
