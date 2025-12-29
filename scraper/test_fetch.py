import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from scraper import fetch_dynamic_html
    
    url = 'https://www.homedepot.com/p/Milwaukee-M18-18V-Lithium-Ion-Cordless-Combo-Kit-6-Tool-with-Two-5-0Ah-Batteries-Charger-and-Tool-Bag-2696-26/309659551'
    
    print(f"Testing Playwright fetch for: {url}")
    print("Please wait...")
    
    try:
        html = await fetch_dynamic_html(url)
        if html:
            print(f"\n✓ SUCCESS! Fetched {len(html)} characters")
            print(f"First 500 chars:\n{html[:500]}")
        else:
            print("\n✗ FAILED - No HTML returned")
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
