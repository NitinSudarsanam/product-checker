import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scraper"))

from scraper import fetch_dynamic_html
from detector import ButtonDetector

async def diagnose():
    # Test Amazon URL
    url = "https://www.amazon.com/CELSIUS-Fitness-Energy-Standard-Variety/dp/B06X6J5266"
    
    print("Fetching HTML...")
    html = await fetch_dynamic_html(url)
    
    if not html:
        print("Failed to get HTML!")
        return
    
    print(f"Got {len(html)} chars of HTML")
    
    # Initialize detector fresh
    detector = ButtonDetector()
    
    # Run detection
    result = detector.detect_all_buttons(html, url)
    
    print("\nDetection Result:")
    print(f"  Add to Cart: {result['add_to_cart']}")
    print(f"  Buy Now: {result['buy_now']}")
    print(f"  Status: {result['status']}")
    print(f"  Add to Cart Method: {result.get('add_to_cart_method')}")
    print(f"  Buy Now Method: {result.get('buy_now_method')}")
    
    # Check if HTML contains expected text
    print("\nHTML Content Check:")
    print(f"  Contains 'Add to Cart': {'Add to Cart' in html}")
    print(f"  Contains 'add-to-cart': {'add-to-cart' in html}")
    print(f"  Contains 'atc': {'atc' in html.lower()}")

asyncio.run(diagnose())
