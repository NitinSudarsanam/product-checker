import asyncio
import aiohttp
from bs4 import BeautifulSoup
from detector import detector

async def test_amazon():
    url = 'https://www.amazon.com/dp/B08N5WRWNW'
    
    # Fetch HTML
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=30) as response:
            html = await response.text()
    
    print(f"HTML length: {len(html)} chars")
    print(f"\n{'='*60}")
    
    # Parse HTML and look for buttons
    soup = BeautifulSoup(html, 'lxml')
    
    # Check for common Amazon button IDs/classes
    add_to_cart_btn = soup.find('input', id='add-to-cart-button')
    buy_now_btn = soup.find('input', id='buy-now-button')
    
    print(f"Direct search for #add-to-cart-button: {add_to_cart_btn is not None}")
    print(f"Direct search for #buy-now-button: {buy_now_btn is not None}")
    
    # Check all buttons
    all_buttons = soup.find_all(['button', 'input'])
    print(f"\nTotal buttons/inputs found: {len(all_buttons)}")
    
    # Show first few buttons
    print("\nFirst 10 button/input elements:")
    for i, btn in enumerate(all_buttons[:10]):
        btn_id = btn.get('id', 'no-id')
        btn_class = btn.get('class', 'no-class')
        btn_text = btn.get_text(strip=True)[:50]
        btn_value = btn.get('value', '')[:50]
        print(f"  {i+1}. Tag:{btn.name} ID:{btn_id} Class:{btn_class}")
        if btn_text:
            print(f"      Text: {btn_text}")
        if btn_value:
            print(f"      Value: {btn_value}")
    
    # Test detector
    print(f"\n{'='*60}")
    print("Detector results:")
    result = detector.detect_all_buttons(html, url)
    print(f"  Add to Cart: {result['add_to_cart']} (method: {result['add_to_cart_method']})")
    print(f"  Buy Now: {result['buy_now']} (method: {result['buy_now_method']})")
    print(f"  Status: {result['status']}")

if __name__ == "__main__":
    asyncio.run(test_amazon())
