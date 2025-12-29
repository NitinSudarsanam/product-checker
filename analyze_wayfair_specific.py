import asyncio
import sys
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent / "scraper"))
from scraper import fetch_dynamic_html
from detector import ButtonDetector

async def analyze():
    url = "https://www.wayfair.com/furniture/pdp/hokku-designs-ziera-6-piece-power-reclining-sectional-with-lay-back-chaise-and-1-reclining-seat-pv10427.html?piid=97582790"
    
    print("Fetching Wayfair page...")
    html = await fetch_dynamic_html(url)
    
    if not html:
        print("Failed to fetch HTML!")
        return
    
    print(f"Got {len(html)} chars of HTML\n")
    
    # Test current detection
    detector = ButtonDetector()
    result = detector.detect_all_buttons(html, url)
    print("Current Detection Result:")
    print(f"  Status: {result['status']}")
    print(f"  Add to Cart: {result['add_to_cart']}")
    print(f"  Method: {result.get('add_to_cart_method')}\n")
    
    # Analyze HTML
    soup = BeautifulSoup(html, 'lxml')
    
    # Look for buttons with "add" text
    print("Searching for buttons with 'add' in text:")
    all_buttons = soup.find_all('button')
    for btn in all_buttons:
        text = btn.get_text().strip().lower()
        if 'add' in text:
            print(f"\nButton text: '{btn.get_text().strip()[:80]}'")
            # Show key attributes
            if btn.get('data-enzyme-id'):
                print(f"  data-enzyme-id: {btn.get('data-enzyme-id')}")
            if btn.get('data-hb-id'):
                print(f"  data-hb-id: {btn.get('data-hb-id')}")
            if btn.get('data-testid'):
                print(f"  data-testid: {btn.get('data-testid')}")
            if btn.get('id'):
                print(f"  id: {btn.get('id')}")
            if btn.get('class'):
                print(f"  classes: {' '.join(btn.get('class')[:3])}")
            if btn.get('aria-label'):
                print(f"  aria-label: {btn.get('aria-label')}")
    
    # Look for any element with text "Add to Cart"
    print("\n\nSearching for ANY element with 'Add to Cart' text:")
    for elem in soup.find_all(text=lambda t: t and 'add to cart' in t.lower()):
        parent = elem.parent
        print(f"\nFound in <{parent.name}>: '{elem.strip()[:60]}'")
        if parent.get('data-enzyme-id'):
            print(f"  data-enzyme-id: {parent.get('data-enzyme-id')}")
        if parent.get('data-hb-id'):
            print(f"  data-hb-id: {parent.get('data-hb-id')}")
        if parent.get('class'):
            print(f"  classes: {' '.join(parent.get('class')[:3])}")

asyncio.run(analyze())
