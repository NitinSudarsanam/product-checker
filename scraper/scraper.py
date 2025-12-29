import asyncio
import time
from datetime import datetime
from typing import Dict, Optional
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth
from detector import detector
import logging
import sys
from pathlib import Path

# Import settings
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
try:
    from app.config import settings
    HEADLESS = settings.scraper_headless
except ImportError:
    # Fallback if running standalone
    HEADLESS = False

# Fix for Windows asyncio subprocess issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Scraper initialized with HEADLESS={HEADLESS}")

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 45
USE_PLAYWRIGHT = True


async def fetch_static_html(url: str, session: aiohttp.ClientSession) -> Optional[str]:
    """Fetch HTML using aiohttp (for static sites)"""
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        async with session.get(url, headers=headers, timeout=timeout, allow_redirects=True, ssl=False) as response:
            if response.status == 200:
                html = await response.text()
                return html
            else:
                logger.warning(f"HTTP {response.status} for {url}")
                return None
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching {url} after {TIMEOUT}s")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Client error fetching {url}: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {type(e).__name__}: {e}")
        return None


async def fetch_dynamic_html(url: str) -> Optional[str]:
    """Fetch HTML using Playwright (for dynamic sites)"""
    browser = None
    context = None
    page = None
    try:
        async with async_playwright() as p:
            # Launch with settings to avoid bot detection
            browser = await p.chromium.launch(
                headless=HEADLESS,  # Configurable via settings.scraper_headless
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # Apply stealth scripts
            stealth = Stealth()
            for script in stealth.enabled_scripts:
                await context.add_init_script(script)
            
            page = await context.new_page()
            
            # Navigate to URL
            logger.info(f"Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT * 1000)
            
            # Wait for the page to be interactive and content to render
            # Try to wait for common "Add to Cart" indicators
            try:
                # Wait for any common add to cart button patterns (with short timeout)
                await page.wait_for_selector('button:has-text("Add to"), button:has-text("add to")', timeout=5000, state='visible')
                logger.info("Add to cart button detected, waiting additional 1s for full render...")
                await page.wait_for_timeout(1000)
            except:
                # If no button found within 5s, wait the full 3s anyway
                logger.info("No add to cart button detected quickly, waiting 3s for content...")
                await page.wait_for_timeout(3000)
            
            # Get HTML content
            html_content = await page.content()
            
            # Cleanup properly
            await page.close()
            await context.close()
            await browser.close()
            return html_content
    
    except PlaywrightTimeout:
        logger.error(f"Playwright timeout for {url} after {TIMEOUT}s")
        # Cleanup
        try:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
        except:
            pass
        return None
    except Exception as e:
        logger.error(f"Playwright error for {url}: {type(e).__name__}: {e}")
        # Cleanup
        try:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
        except:
            pass
        return None


async def scrape_url(url: str, use_playwright: bool = USE_PLAYWRIGHT) -> Dict:
    """
    Scrape a URL and detect buy buttons
    
    Args:
        url: URL to scrape
        use_playwright: Whether to use Playwright for dynamic rendering
    
    Returns:
        Dict containing scan results
    """
    start_time = time.time()
    
    result = {
        "url": url,
        "scanned_at": datetime.utcnow(),
        "add_to_cart": False,
        "buy_now": False,
        "status": "error",
        "error_message": None,
        "response_time": None
    }
    
    try:
        logger.info(f"Scraping {url}")
        
        # Fetch HTML content
        html_content = None
        
        if use_playwright:
            # Try Playwright first (for dynamic sites)
            try:
                logger.info(f"Using Playwright for {url}")
                html_content = await fetch_dynamic_html(url)
                if html_content:
                    logger.info(f"Playwright returned {len(html_content)} chars for {url}")
                else:
                    logger.warning(f"Playwright returned None for {url}")
            except Exception as e:
                logger.error(f"Playwright exception for {url}: {type(e).__name__}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                html_content = None
        
        # Use static fetching if Playwright not used or failed
        if not html_content:
            logger.info(f"Using static fetch for {url}")
            try:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    html_content = await fetch_static_html(url, session)
                if html_content:
                    logger.info(f"Static fetch returned {len(html_content)} chars for {url}")
                else:
                    logger.warning(f"Static fetch returned None for {url}")
            except Exception as e:
                logger.error(f"Static fetch exception for {url}: {type(e).__name__}: {e}")
                html_content = None
        
        if not html_content:
            logger.error(f"All fetch methods failed for {url}")
            result["error_message"] = "Failed to fetch HTML content"
            result["status"] = "error"
            return result
        
        # Detect buttons
        detection_result = detector.detect_all_buttons(html_content, url)
        
        # Update result
        result.update({
            "add_to_cart": detection_result["add_to_cart"],
            "buy_now": detection_result["buy_now"],
            "status": detection_result["status"],
            "error_message": None
        })
        
        logger.info(f"Scan complete for {url}: status={detection_result['status']}, "
                   f"add_to_cart={detection_result['add_to_cart']}, "
                   f"buy_now={detection_result['buy_now']}, "
                   f"HTML length={len(html_content)}, "
                   f"methods: {detection_result.get('add_to_cart_method', 'N/A')}, "
                   f"{detection_result.get('buy_now_method', 'N/A')}")
    
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        result["error_message"] = str(e)
        result["status"] = "error"
    
    finally:
        # Calculate response time
        result["response_time"] = round(time.time() - start_time, 2)
    
    return result


async def scrape_multiple_urls(urls: list, use_playwright: bool = USE_PLAYWRIGHT, max_concurrent: int = 5) -> list:
    """
    Scrape multiple URLs concurrently
    
    Args:
        urls: List of URLs to scrape
        use_playwright: Whether to use Playwright
        max_concurrent: Maximum concurrent requests
    
    Returns:
        List of scan results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def scrape_with_semaphore(url):
        async with semaphore:
            return await scrape_url(url, use_playwright)
    
    tasks = [scrape_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    return results


# Test function
async def test_scraper():
    """Test the scraper with sample URLs"""
    test_urls = [
        "https://www.amazon.com/dp/B08N5WRWNW",  # Amazon product
        "https://www.example.com",  # Simple static site
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print('='*60)
        
        result = await scrape_url(url)
        
        print(f"Status: {result['status']}")
        print(f"Add to Cart: {result['add_to_cart']}")
        print(f"Buy Now: {result['buy_now']}")
        print(f"Response Time: {result['response_time']}s")
        if result['error_message']:
            print(f"Error: {result['error_message']}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_scraper())
