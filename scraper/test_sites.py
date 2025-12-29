import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from scraper import scrape_url
    
    test_urls = [
        'https://www.wayfair.com/furniture/pdp/mercury-row-caila-sideboard-w006518589.html',
        'https://www.homedepot.com/p/Milwaukee-M18-18V-Lithium-Ion-Cordless-Combo-Kit-6-Tool-with-Two-5-0Ah-Batteries-Charger-and-Tool-Bag-2696-26/309659551'
    ]
    
    for url in test_urls:
        print(f"\n{'='*70}")
        print(f"Testing: {url}")
        print('='*70)
        
        result = await scrape_url(url, use_playwright=True)
        
        print(f"Status: {result['status']}")
        print(f"Add to Cart: {result['add_to_cart']}")
        print(f"Buy Now: {result['buy_now']}")
        print(f"Response Time: {result['response_time']}s")
        if result.get("error_message"):
            print(f"Error: {result['error_message']}")

if __name__ == "__main__":
    asyncio.run(test())
