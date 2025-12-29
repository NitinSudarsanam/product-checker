import asyncio
import sys
from pathlib import Path

# Add scraper to path
sys.path.insert(0, str(Path(__file__).parent / "scraper"))
from scraper import scrape_url

async def test_urls():
    # Test URLs
    wayfair_url = "https://www.wayfair.com/furniture/pdp/latitude-run-sargon-upholstered-low-profile-standard-bed-w003780954.html"
    homedepot_url = "https://www.homedepot.com/p/DEWALT-20V-MAX-XR-Cordless-Brushless-1-2-in-Hammer-Drill-Driver-Tool-Only-DCD999B/308040476"
    
    print("=" * 70)
    print("Testing Wayfair...")
    print("=" * 70)
    wayfair_result = await scrape_url(wayfair_url, use_playwright=True)
    print(f"Status: {wayfair_result['status']}")
    print(f"Add to Cart: {wayfair_result['add_to_cart']}")
    print(f"Buy Now: {wayfair_result['buy_now']}")
    print(f"HTML Length: {len(wayfair_result.get('html', ''))} chars")
    print(f"Error: {wayfair_result.get('error_message', 'None')}")
    
    print("\n" + "=" * 70)
    print("Testing Home Depot...")
    print("=" * 70)
    homedepot_result = await scrape_url(homedepot_url, use_playwright=True)
    print(f"Status: {homedepot_result['status']}")
    print(f"Add to Cart: {homedepot_result['add_to_cart']}")
    print(f"Buy Now: {homedepot_result['buy_now']}")
    print(f"HTML Length: {len(homedepot_result.get('html', ''))} chars")
    print(f"Error: {homedepot_result.get('error_message', 'None')}")

asyncio.run(test_urls())
