import asyncio
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scraper"))

async def deep_analyze_wayfair():
    url = "https://www.wayfair.com/furniture/pdp/latitude-run-sargon-upholstered-low-profile-standard-bed-w003780954.html"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Apply stealth scripts
        stealth = Stealth()
        for script in stealth.enabled_scripts:
            await context.add_init_script(script)
        
        page = await context.new_page()
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait longer for JavaScript to fully load
        print("Waiting 10 seconds for dynamic content...")
        await page.wait_for_timeout(10000)
        
        html = await page.content()
        print(f"\nGot {len(html)} chars of HTML")
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Search for anything with "cart" in attributes or text
        print("\nSearching for elements with 'cart' in data attributes:")
        for elem in soup.find_all(attrs=lambda x: x and any('cart' in str(v).lower() for v in x.values() if v)):
            print(f"  {elem.name}: {dict(list(elem.attrs.items())[:3])} - '{elem.get_text()[:50]}'")
        
        print("\nSearching for elements with text containing 'add to':")
        for elem in soup.find_all(text=lambda t: t and 'add to' in t.lower()):
            parent = elem.parent
            print(f"  {parent.name}: {dict(list(parent.attrs.items())[:3])} - '{elem[:60]}'")
        
        await browser.close()

asyncio.run(deep_analyze_wayfair())
