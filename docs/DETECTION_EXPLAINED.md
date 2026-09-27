# How Availability Is Decided

Each URL ends up `available`, `unavailable`, or `error`:

- **available**: a usable Add to Cart or Buy Now control was found for the product (or for at least one variant).
- **unavailable**: the page loaded, but no usable buy control was found, or product-level "out of stock" wording overrode it.
- **error**: the page couldn't be read. Fetch failures, timeouts, and bot-block pages all land here, so a blocked request is never reported as out of stock.

The code is in `scraper/scraper.py` (fetching, live-page checks, variants, combining) and `scraper/detector.py` (HTML rules).

## 1. Fetching the page

`scrape_url()` tries these in order and uses the first one that returns HTML that isn't a block page:

1. **Playwright.** A real browser: Chromium, or Firefox for Staples and Office Depot, which hit HTTP/2 errors in Chromium.
   - Stealth scripts, a Windows Chrome user agent, a 1920×1080 viewport, and US locale and time zone.
   - Loads saved cookies from `scraper/storage_state/<domain>.json` if present (see `bootstrap_state.py`).
   - Skips images, fonts, and media to load faster.
   - Waits up to 5 s (8 s on Amazon and Walmart) for a buy button to appear, then takes the HTML.
   - If blocked, retries once without saved cookies. For Walmart and Target, if `SCRAPINGBEE_API_KEY` is set, it then retries through ScrapingBee's proxy.
2. **ScrapingBee**, if `SCRAPINGBEE_API_KEY` is set. See [../SCRAPINGBEE.md](../SCRAPINGBEE.md).
3. **Plain HTTP** (aiohttp). No JavaScript, so it only helps on server-rendered pages.

Set `SCRAPER_SCRAPINGBEE_FIRST=true` to try ScrapingBee before Playwright.

## 2. Spotting block pages

`_looks_blocked_html()` checks the page title and the first 120 KB of HTML for phrases such as:

`robot or human`, `verify you are human`, `captcha`, `enter the characters you see below`, `automated access`, `access denied`, `page not found`, `currently not available in your country`, `oops!! something went wrong`

It also catches Amazon's "dogs of Amazon" error page. A match makes the result `error` with `error_message: "blocked:<phrase>"`. If `SCRAPER_SCREENSHOT_DIR` is set, Playwright saves a screenshot of the block page.

## 3. Finding buy buttons in the HTML

`ButtonDetector.detect_button()` runs separately for `add_to_cart` and `buy_now`, using `scraper/detection_rules.json`. It stops at the first match:

1. **Site rules.** If the page's domain contains a key under `domains` (for example `walmart.com`), try that site's `selectors`, then its `text`.
2. **Generic selectors** from `css_selectors`, e.g. `#add-to-cart`, `[data-action='add-to-cart']`.
3. **Generic text** from `text_patterns`, e.g. "add to cart", "add to bag", "buy now". Checked against the text and the `value`, `title`, `aria-label`, and `data-text` attributes of `<button>`, `<a>`, `<input>`, and any `<div>`/`<span>` that has `role="button"` or a class containing "btn" or "button". Matching is case-insensitive and partial by default (see `settings` in the rules file).

A match only counts if the element looks usable. It's rejected if it has:

- a `disabled`, `aria-disabled="true"`, `aria-busy="true"`, or `data-disabled="true"` attribute,
- a class like `disabled`, `out-of-stock`, `sold-out`, `unavailable`, `oos`,
- text like "notify me", "join waitlist", "email me", "sold out".

Sites with their own rules: Amazon, Walmart, eBay, Shopify, Target, Wayfair, Home Depot, Kohl's, Lowe's, Office Depot, Overstock, Staples, Best Buy, Etsy, Costco.

If `detection_rules.json` is missing or invalid, the detector logs an error and uses small built-in fallback rules instead of crashing.

## 4. Out-of-stock override

If a button was found, the detector also looks for explicit unavailability wording ("sold out", "out of stock", "currently unavailable", "notify me when available", "no longer available", and others). It only searches the product area of the page, not the whole document. Examples are `#buybox` and `main`, plus per-site containers for Walmart, Wayfair, Amazon, Home Depot, Kohl's, Lowe's, Office Depot, Overstock, and Staples. This keeps "out of stock" in a recommendations carousel from killing a real buy button. "Out of stock" next to "other sellers" or "compare with" is also ignored.

If the wording is found, the result becomes `unavailable` with `unavailability_override: true`.

## 5. Checks on the live page (Playwright only)

Saved HTML can be misleading. A button can be in the markup but hidden, greyed out, or still loading. When Playwright fetched the page, two extra checks run in the real browser.

**Is a buy button actually clickable right now?** A JavaScript check looks for common add-to-cart and buy-now elements and requires one that is visible, not disabled, not `aria-busy`, has opacity above 0.15, accepts pointer events, and has a real size. It samples twice about 280 ms apart, so a button that flashes enabled while the page loads doesn't count.

**Variants.** With `SCRAPER_CHECK_VARIANTS=true` (the default), the scraper tries each product option and re-runs the clickable check after each one:

- `<select>` dropdowns, skipping ones for country, quantity, sort, shipping and similar. On Amazon and Walmart it also skips subscription, delivery-date, and very long non-variant lists.
- radio button groups
- `role="listbox"` / `role="option"` widgets

Limits keep this bounded: at most 25 variants (30 on Amazon and Walmart), and 45 s total (30 s on Amazon and Walmart).

## 6. Combining the signals

In `scrape_url()`:

1. **Variants were found:** `available` if any variant is purchasable, unless the out-of-stock override fired.
2. **No variants:** use the HTML detection result. If Playwright's live check found no clickable button but the HTML said there was one, the live check wins and the result is `unavailable`.
3. **Wayfair via ScrapingBee:** if ScrapingBee's HTML says `available`, Playwright re-checks the page and its answer wins, because ScrapingBee's Wayfair snapshots are often stale.

`scrape_method` on the result records which method produced the final answer, and `html_primary_source` records which returned HTML first.

## Adding or fixing a site

Edit `scraper/detection_rules.json`:

```json
{
  "add_to_cart": {
    "domains": {
      "newsite.com": {
        "selectors": ["button#add-to-cart", "[data-testid='atc-button']"],
        "text": ["Add to Cart"]
      }
    }
  }
}
```

In Docker the `scraper/` folder is mounted into the containers, so restart the worker (`docker compose restart worker`) to pick up the change. No rebuild is needed.

If the page loads but the button isn't in the fetched HTML, the problem is fetching or blocking, not rules. Set `SCRAPER_SCREENSHOT_DIR` and look at what the browser actually saw.

## Known site behaviour

From the test runs saved in `scraper/test_artifacts/` (May 2026):

- **Blocked often:** Amazon (CAPTCHA or error page), Target (CAPTCHA), Walmart ("robot or human"), Kohl's ("access denied"), Staples (CAPTCHA). Saved cookies from `bootstrap_state.py` and ScrapingBee help, but only sometimes.
- **Home Depot** often returns a small error page to automated browsers.
- **Office Depot** has had navigation errors.
- **Wayfair** and smaller Shopify-style stores usually work.

Blocking gets worse from Docker and from cloud servers. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#scans-blocked-in-docker-but-not-locally).
