import asyncio
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add scraper to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scraper"))
from scraper import fetch_dynamic_html
from detector import ButtonDetector

async def debug_wayfair():
    url = "https://www.wayfair.com/furniture/pdp/latitude-run-sargon-upholstered-low-profile-standard-bed-w003780954.html"
    
    print("Fetching Wayfair page with Playwright...")
    html = await fetch_dynamic_html(url)
    
    if not html:
        print("No HTML returned!")
        return
    
    print(f"Got {len(html)} chars of HTML\n")
    
    # Run detector
    print("Running detector...")
    detector = ButtonDetector()
    result = detector.detect_all_buttons(html, url)
    print(f"Detection result: {result}\n")
    
    # Manual check
    soup = BeautifulSoup(html, 'lxml')
    
    selectors = [
        "button[data-enzyme-id='AddToCart']",
        "button[data-hb-id='AddToCartButton']",
        "#btn-add-to-cart"
    ]
    
    print("Manual selector checks:")
    for selector in selectors:
        found = soup.select(selector)
        print(f"  {selector}: {len(found)} found")
        if found:
            for i, el in enumerate(found[:2]):
                print(f"    Match {i+1}: {el.get_text()[:60]}")
    
    # Search for any button with "add to cart" text
    print("\nSearching for buttons with 'add to cart' text:")
    all_buttons = soup.find_all('button')
    for btn in all_buttons:
        text = btn.get_text().strip().lower()
        if 'add to cart' in text:
            attrs = dict(list(btn.attrs.items())[:3])
            print(f"  Found: {btn.name} {attrs} - '{btn.get_text()[:50]}'")

asyncio.run(debug_wayfair())
