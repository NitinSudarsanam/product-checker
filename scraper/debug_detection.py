import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from scraper import scrape_url
    from bs4 import BeautifulSoup
    
    test_urls = [
        ('Walmart', 'https://www.walmart.com/ip/Premier-Protein-Shake-Chocolate-30g-Protein-1g-Sugar-24-Vitamins-Minerals-Nutrients-Support-Immune-Health-11-5-Fl-Oz-12-Pack/21130579'),
        ('Home Depot', 'https://www.homedepot.com/p/DEWALT-20V-MAX-XR-Cordless-Brushless-Drill-Driver-and-Impact-Driver-2-Tool-Combo-Kit-with-2-2-0-Ah-Batteries-Charger-and-Bag-DCK240C2/308360029')
    ]
    
    for site, url in test_urls:
        print(f"\n{'='*70}")
        print(f"Testing {site}: {url}")
        print('='*70)
        
        result = await scrape_url(url, use_playwright=True)
        
        print(f"Status: {result['status']}")
        print(f"Add to Cart: {result['add_to_cart']}")
        print(f"Buy Now: {result['buy_now']}")
        print(f"Error: {result.get('error_message', 'None')}")
        
        # If failed, let's check what buttons we actually found
        if result['status'] == 'unavailable' or result['status'] == 'error':
            # Try to fetch again and analyze
            from scraper import fetch_dynamic_html
            html = await fetch_dynamic_html(url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                buttons = soup.find_all(['button', 'input', 'a'], limit=30)
                
                print(f"\nFound {len(buttons)} button/input/link elements:")
                for i, btn in enumerate(buttons[:15]):
                    btn_text = btn.get_text(strip=True)[:50]
                    btn_id = btn.get('id', '')
                    btn_class = ' '.join(btn.get('class', []))[:60]
                    btn_data = {k: v for k, v in btn.attrs.items() if k.startswith('data-')}
                    
                    if 'cart' in btn_text.lower() or 'add' in btn_text.lower() or 'buy' in btn_text.lower():
                        print(f"\n  *** RELEVANT: {btn.name} ***")
                        print(f"      Text: {btn_text}")
                        print(f"      ID: {btn_id}")
                        print(f"      Class: {btn_class}")
                        if btn_data:
                            print(f"      Data attrs: {btn_data}")

if __name__ == "__main__":
    asyncio.run(test())
