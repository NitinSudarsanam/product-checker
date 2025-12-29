import asyncio
from scraper import scrape_url

async def test():
    url = 'https://www.amazon.com/dp/B08N5WRWNW'
    print(f"Testing URL: {url}")
    
    # Import fetch function
    from scraper import fetch_dynamic_html
    html = await fetch_dynamic_html(url)
    
    if html:
        print(f"HTML length: {len(html)}")
        print("\nFirst 2000 chars:")
        print(html[:2000])
        print("\n\n...searching for 'add-to-cart' or 'buy'...")
        if 'add-to-cart' in html.lower():
            print("✓ Found 'add-to-cart' in HTML")
        if 'buy' in html.lower():
            print("✓ Found 'buy' in HTML")
        
        # Save to file
        with open('amazon_sample.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\nSaved to amazon_sample.html")

asyncio.run(test())
