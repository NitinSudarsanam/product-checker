import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from detector import detector

async def test_with_playwright():
    url = 'https://www.amazon.com/dp/B08N5WRWNW'
    
    print(f"Testing {url} with Playwright...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            html = await page.content()
            print(f"HTML length: {len(html)} chars")
            
            # Parse and check
            soup = BeautifulSoup(html, 'lxml')
            add_to_cart_btn = soup.find('input', id='add-to-cart-button')
            buy_now_btn = soup.find('input', id='buy-now-button')
            
            print(f"\nDirect search for #add-to-cart-button: {add_to_cart_btn is not None}")
            print(f"Direct search for #buy-now-button: {buy_now_btn is not None}")
            
            if add_to_cart_btn:
                print(f"  Add to Cart button value: {add_to_cart_btn.get('value', 'N/A')}")
            if buy_now_btn:
                print(f"  Buy Now button value: {buy_now_btn.get('value', 'N/A')}")
            
            # Test detector
            print(f"\n{'='*60}")
            print("Detector results:")
            result = detector.detect_all_buttons(html, url)
            print(f"  Add to Cart: {result['add_to_cart']} (method: {result['add_to_cart_method']})")
            print(f"  Buy Now: {result['buy_now']} (method: {result['buy_now_method']})")
            print(f"  Status: {result['status']}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_with_playwright())
