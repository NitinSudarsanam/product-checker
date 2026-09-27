import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scraper"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from scraper import scrape_url
from app.config import settings

async def test():
    # Test with a Walmart URL that should work
    walmart_url = "https://www.walmart.com/ip/Restored-Apple-iPhone-11-64GB-Black-Fully-Unlocked-Refurbished/329207552"
    
    print(f"Settings check:")
    print(f"  SCRAPER_HEADLESS: {settings.scraper_headless}")
    print(f"  SCRAPER_USE_PLAYWRIGHT: {settings.scraper_use_playwright}")
    print()
    
    print("Testing Walmart URL...")
    result = await scrape_url(walmart_url, use_playwright=True)
    
    print("\n" + "="*70)
    print("RESULT:")
    print("="*70)
    print(f"Status: {result['status']}")
    print(f"Add to Cart: {result['add_to_cart']}")
    print(f"Buy Now: {result['buy_now']}")
    print(f"Error: {result.get('error_message', 'None')}")
    print(f"Response Time: {result['response_time']}s")
    print("="*70)

asyncio.run(test())
