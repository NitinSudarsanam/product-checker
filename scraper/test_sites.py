import asyncio
import sys
import time
import os
from datetime import datetime
from pathlib import Path
sys.path.insert(0, '.')

async def test():
    from scraper import scrape_url
    from golden_urls import iter_all_golden_urls
    from screenshot_urls import _shot
    
    env_urls = os.environ.get("TEST_URLS", "").strip()
    test_urls = [u.strip() for u in env_urls.split(",") if u.strip()] if env_urls else iter_all_golden_urls()

    out_dir = Path(__file__).parent / "test_artifacts" / datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for url in test_urls:
        print(f"\n{'='*70}")
        print(f"Testing: {url}")
        print('='*70)

        # Always capture a screenshot for verification (even if blocked/challenged).
        try:
            t0 = time.time()
            shot_path = await _shot(url, out_dir, timeout_ms=90_000, full_page=False)
            print(f"Screenshot: {shot_path} ({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"Screenshot: FAIL ({type(e).__name__}: {e})")
        
        result = await scrape_url(url, use_playwright=True)
        
        print(f"Status: {result['status']}")
        print(f"Add to Cart: {result['add_to_cart']}")
        print(f"Buy Now: {result['buy_now']}")
        if result.get("variants"):
            available = sum(1 for v in (result.get("variants") or {}).values() if v == "available")
            print(f"Variants: {available}/{len(result.get('variants') or {})} available")
        print(f"Response Time: {result['response_time']}s")
        if result.get("error_message"):
            print(f"Error: {result['error_message']}")

if __name__ == "__main__":
    asyncio.run(test())
