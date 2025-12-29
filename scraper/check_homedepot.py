import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from scraper import fetch_dynamic_html
    from bs4 import BeautifulSoup
    
    url = 'https://www.homedepot.com/p/DEWALT-20V-MAX-XR-Cordless-Brushless-Drill-Driver-and-Impact-Driver-2-Tool-Combo-Kit-with-2-2-0-Ah-Batteries-Charger-and-Bag-DCK240C2/308360029'
    
    print("Fetching Home Depot page...")
    html = await fetch_dynamic_html(url)
    
    if html:
        print(f"HTML length: {len(html)}")
        
        # Check if it's a bot block page
        if len(html) < 10000:
            print("\n⚠️ WARNING: Short HTML suggests bot blocking")
            print("First 1000 chars:")
            print(html[:1000])
        else:
            soup = BeautifulSoup(html, 'lxml')
            
            # Search for add to cart buttons
            print("\nSearching for 'add to cart' related elements...")
            
            # Check for specific selectors
            selectors = [
                "button[data-testid='add-to-cart']",
                "button#add-to-cart-btn",
                ".bttn__buy-now",
                "button[data-component='add-to-cart-button']",
                "button.bttn--primary",
                "[data-automation-id='add-to-cart']"
            ]
            
            for sel in selectors:
                found = soup.select(sel)
                if found:
                    print(f"✓ Found with selector '{sel}': {len(found)} elements")
                    print(f"  Text: {found[0].get_text(strip=True)[:50]}")
            
            # Search by text
            all_buttons = soup.find_all(['button', 'input'])
            print(f"\nTotal buttons/inputs: {len(all_buttons)}")
            
            cart_buttons = []
            for btn in all_buttons:
                text = btn.get_text(strip=True).lower()
                if 'add' in text and 'cart' in text:
                    cart_buttons.append(btn)
                    print(f"\n✓ Found button with 'add' and 'cart':")
                    print(f"  Text: {btn.get_text(strip=True)}")
                    print(f"  ID: {btn.get('id', 'N/A')}")
                    print(f"  Classes: {btn.get('class', [])}")
                    print(f"  Data attrs: {[k for k in btn.attrs.keys() if k.startswith('data-')]}")
            
            if not cart_buttons:
                print("\n❌ No 'add to cart' buttons found")
                print("\nShowing first 10 buttons:")
                for i, btn in enumerate(all_buttons[:10]):
                    print(f"\n  {i+1}. {btn.name}")
                    print(f"     Text: {btn.get_text(strip=True)[:50]}")
                    print(f"     Classes: {btn.get('class', [])}")

if __name__ == "__main__":
    asyncio.run(test())
