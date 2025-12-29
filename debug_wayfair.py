import asyncio
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add scraper to path
sys.path.insert(0, str(Path(__file__).parent / "scraper"))
from scraper import scrape_url

async def debug_wayfair():
    url = "https://www.wayfair.com/furniture/pdp/latitude-run-sargon-upholstered-low-profile-standard-bed-w003780954.html"
    
    print("Fetching Wayfair page...")
    result = await scrape_url(url, use_playwright=True)
    
    html = result.get('raw_html', '')
    if not html:
        print("No HTML returned!")
        return
    
    print(f"Got {len(html)} chars of HTML")
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Check for the selectors we have in detection_rules.json
    selectors = [
        "button[data-enzyme-id='AddToCart']",
        "button[data-hb-id='AddToCartButton']",
        "#btn-add-to-cart"
    ]
    
    print("\nChecking Wayfair selectors:")
    for selector in selectors:
        found = soup.select(selector)
        print(f"  {selector}: {len(found)} found")
        if found:
            print(f"    First match: {found[0].name} - {found[0].get('class', [])} - {found[0].get_text()[:50]}")
    
    # Look for any buttons with "cart" in them
    print("\nAll buttons with 'cart' or 'add' (first 10):")
    all_buttons = soup.find_all('button')
    cart_buttons = [b for b in all_buttons if 'cart' in str(b).lower() or 'add' in str(b).lower()]
    for i, btn in enumerate(cart_buttons[:10]):
        attrs = ' '.join([f'{k}="{v}"' for k, v in list(btn.attrs.items())[:3]])
        print(f"  {i+1}. <button {attrs}...> {btn.get_text()[:40]}")

asyncio.run(debug_wayfair())
