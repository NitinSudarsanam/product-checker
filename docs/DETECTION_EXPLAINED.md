# Product Detection System - How It Works

## Overview
The scraper detects "Add to Cart" and "Buy Now" buttons on e-commerce websites using multiple strategies.

## Detection Methods

### 1. **Domain-Specific Rules** (Highest Priority)
Each major e-commerce site has custom CSS selectors and text patterns:

**Amazon:**
- Selectors: `#add-to-cart-button`, `input#add-to-cart-button`
- Text: "Add to Cart"
- **Current Status**: ❌ Bot-blocked - Amazon has aggressive CAPTCHA protection that blocks automated browsers, even with stealth mode. We get a 2-3KB CAPTCHA page instead of the actual product page.

**Walmart:**
- Selectors: Multiple including `button[data-automation-id='atc-btn']`
- Text: "Add to cart", "Add to Cart"
- **Current Status**: ✅ Works with non-headless browser

**Wayfair:**
- Selectors: `button[data-enzyme-id='AddToCart']`, `button[data-hb-id='AddToCartButton']`
- **Current Status**: ✅ Works well

**Home Depot:**
- Selectors: Multiple including `button[data-testid='add-to-cart']`
- **Current Status**: ⚠️ Partially blocked - Even with visible browser, returns error pages (~2KB)

### 2. **Generic CSS Selectors** (Medium Priority)
If domain-specific rules don't match, try generic patterns:
- `#add-to-cart`, `.add-to-cart`, `.add-to-cart-button`
- `button[id*='add']`, `button[class*='add']`
- `[data-action='add-to-cart']`

### 3. **Text Pattern Matching** (Lowest Priority)
Searches button text content for keywords:
- "add to cart", "add to bag", "add to basket"
- "buy now", "buy it now"
- Case-insensitive, partial match enabled

## Bot Protection Issues

### Why Amazon Fails:
1. **CAPTCHA**: Amazon shows a CAPTCHA page instead of the product page
2. **Fingerprinting**: Detects Playwright/automation even with stealth mode
3. **Solution Options**:
   - Use Amazon Product Advertising API (official)
   - Residential proxy network (expensive)
   - Browser with more realistic behavior (very complex)

### Why Home Depot Fails:
1. **Error Page**: Returns a generic "Error Page" HTML
2. **IP/Device Fingerprinting**: Blocks automated access
3. **Solution**: Similar to Amazon - needs proxies or API access

### What Works:
- **Walmart**: With non-headless browser (visible window)
- **Wayfair**: Works well with Playwright
- **Smaller e-commerce sites**: Usually work fine

## Technical Details

### Playwright Settings:
- **Headless**: False (visible browser = better bot evasion)
- **Stealth Mode**: Enabled (playwright-stealth)
- **User Agent**: Modern Chrome on Windows
- **Timeout**: 45 seconds

### Page Load Strategy:
1. Navigate to URL with `domcontentloaded` event
2. Wait additional 3 seconds for dynamic content
3. Extract full HTML content
4. Parse with BeautifulSoup (lxml parser)
5. Apply detection rules in priority order

## Configuration

Edit `.env` to control behavior:
```env
SCRAPER_USE_PLAYWRIGHT=true  # Use browser automation
SCRAPER_TIMEOUT=45           # Max wait time per page
SCRAPER_HEADLESS=false       # false = visible browser
```

## Recommendations

**For Production Use:**
1. ✅ Works out-of-box: Walmart, Wayfair, Target, eBay
2. ⚠️ Needs work: Amazon, Home Depot (use official APIs)
3. 🔧 Best practice: Combine this scraper with official APIs for major retailers
