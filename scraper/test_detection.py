import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    # Import after path is set
    from scraper import scrape_url
    
    url = 'https://www.amazon.com/dp/B08N5WRWNW'
    print(f"Testing URL: {url}")
    print("Using Playwright...")
    
    result = await scrape_url(url, use_playwright=True)
    print(f"\nResults:")
    print(f"  Status: {result['status']}")
    print(f"  Add to Cart: {result['add_to_cart']}")
    print(f"  Buy Now: {result['buy_now']}")
    print(f"  Response Time: {result['response_time']}s")
    if result.get("error_message"):
        print(f"  Error: {result['error_message']}")

if __name__ == "__main__":
    asyncio.run(test())
