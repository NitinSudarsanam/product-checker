import asyncio
import time
import os
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import aiohttp
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth
try:
    # When `scraper` is imported as a package (e.g. inside Docker workers)
    from .detector import detector
except ImportError:
    # When running this file directly / legacy path hacks
    from detector import detector
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
try:
    from app.config import settings
    HEADLESS = settings.scraper_headless
    SCRAPINGBEE_API_KEY = settings.scrapingbee_api_key
    SCRAPINGBEE_COUNTRY = settings.scrapingbee_country_code
    TIMEOUT = settings.scraper_timeout
    CHECK_VARIANTS = settings.scraper_check_variants
    PLAYWRIGHT_MAX_CONCURRENT = getattr(settings, "playwright_max_concurrent", 2)
    SCRAPINGBEE_MAX_WORKERS = getattr(settings, "scrapingbee_max_workers", 5)
    SCRAPINGBEE_MAX_CONCURRENT = getattr(settings, "scrapingbee_max_concurrent", 5)
    SCRAPINGBEE_RPS = float(getattr(settings, "scrapingbee_rps", 0.0) or 0.0)
    SCRAPER_SCRAPINGBEE_FIRST = bool(getattr(settings, "scraper_scrapingbee_first", False))
    SCRAPER_STATIC_SSL_VERIFY = bool(getattr(settings, "scraper_static_ssl_verify", True))
except ImportError:
    HEADLESS = True
    SCRAPINGBEE_API_KEY = os.environ.get("SCRAPINGBEE_API_KEY", "")
    SCRAPINGBEE_COUNTRY = os.environ.get("SCRAPINGBEE_COUNTRY_CODE", "us")
    TIMEOUT = 45
    CHECK_VARIANTS = os.environ.get("SCRAPER_CHECK_VARIANTS", "true").lower() == "true"
    PLAYWRIGHT_MAX_CONCURRENT = int(os.environ.get("PLAYWRIGHT_MAX_CONCURRENT", "2") or "2")
    SCRAPINGBEE_MAX_WORKERS = int(os.environ.get("SCRAPINGBEE_MAX_WORKERS", "5") or "5")
    SCRAPINGBEE_MAX_CONCURRENT = int(os.environ.get("SCRAPINGBEE_MAX_CONCURRENT", str(SCRAPINGBEE_MAX_WORKERS)) or str(SCRAPINGBEE_MAX_WORKERS))
    try:
        SCRAPINGBEE_RPS = float(os.environ.get("SCRAPINGBEE_RPS", "0") or "0")
    except ValueError:
        SCRAPINGBEE_RPS = 0.0
    SCRAPER_SCRAPINGBEE_FIRST = os.environ.get("SCRAPER_SCRAPINGBEE_FIRST", "false").lower() in (
        "1", "true", "yes",
    )
    SCRAPER_STATIC_SSL_VERIFY = os.environ.get("SCRAPER_STATIC_SSL_VERIFY", "true").lower() in (
        "1", "true", "yes",
    )

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(
    f"Scraper: HEADLESS={HEADLESS} "
    f"ScrapingBee={'on' if SCRAPINGBEE_API_KEY else 'off'} "
    f"bee_key_len={len(SCRAPINGBEE_API_KEY) if SCRAPINGBEE_API_KEY else 0} "
    f"bee_first={SCRAPER_SCRAPINGBEE_FIRST} "
    f"Variants={'on' if CHECK_VARIANTS else 'off'}"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

SCRAPER_STORAGE_STATE_DIR = os.environ.get(
    "SCRAPER_STORAGE_STATE_DIR",
    str(Path(__file__).parent / "storage_state"),
).strip() or str(Path(__file__).parent / "storage_state")

SCRAPER_SCREENSHOT_DIR = os.environ.get(
    "SCRAPER_SCREENSHOT_DIR",
    "",
).strip()


def _domain_key(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host or "unknown"


def _storage_state_path_for(url: str) -> Path:
    d = Path(SCRAPER_STORAGE_STATE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_domain_key(url)}.json"


def _screenshot_path_for(url: str, suffix: str) -> Optional[Path]:
    if not SCRAPER_SCREENSHOT_DIR:
        return None
    d = Path(SCRAPER_SCREENSHOT_DIR)
    d.mkdir(parents=True, exist_ok=True)
    slug = url.replace("https://", "").replace("http://", "")
    slug = "".join(c if c.isalnum() or c in "._-" else "_" for c in slug)[:140].strip("_") or "url"
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return d / f"{ts}__{_domain_key(url)}__{slug}__{suffix}.png"

_bee_executor = ThreadPoolExecutor(max_workers=SCRAPINGBEE_MAX_WORKERS, thread_name_prefix="scrapingbee")
_scrapingbee_semaphore = asyncio.Semaphore(max(1, SCRAPINGBEE_MAX_CONCURRENT))
_playwright_semaphore = asyncio.Semaphore(max(1, PLAYWRIGHT_MAX_CONCURRENT))

_sb_rate_lock = asyncio.Lock()
_sb_next_allowed_at: float = 0.0


async def _scrapingbee_rate_limit_wait():
    """Best-effort client-side limiter to reduce 429 bursts on low tiers."""
    global _sb_next_allowed_at
    if SCRAPINGBEE_RPS <= 0:
        return
    min_interval = 1.0 / SCRAPINGBEE_RPS
    async with _sb_rate_lock:
        now = time.time()
        wait_s = max(0.0, _sb_next_allowed_at - now)
        if wait_s > 0:
            await asyncio.sleep(wait_s)
        _sb_next_allowed_at = max(_sb_next_allowed_at, now) + min_interval

# Select names/ids that are NOT variant selectors
_SKIP_SELECT_KEYWORDS = {
    'country', 'state', 'province', 'region', 'shipping', 'currency',
    'language', 'locale', 'qty', 'quantity', 'sort', 'filter', 'per_page',
    'review', 'rating', 'billing', 'address',
}

# Amazon/Walmart often expose huge non-product <select>s (S&S month, "url" ASIN list, etc.)
_MEGA_EXTRA_SKIP_SUBSTRINGS = (
    'url', 'asin', 'subscribe', 'recurring', 'installment', 'audible',
    'onlinemonth', 'offlinemonth', 'onlineday', 'offlineday', 'onlineyear', 'offlineyear',
    'month', 'day', 'year', 'date', 'dob',
    'rcx', 'swn-', 'prime', 'deliverydate', 'giftoption',
    'quantity', 'message', 'language', 'currency',
)

# If name/id hints at real product dimensions, probe even on megastores
_VARIANT_DIM_HINTS = (
    'size', 'color', 'colour', 'style', 'width', 'length', 'pack', 'scent',
    'flavor', 'flavour', 'count', 'twister', 'variation', 'pattern', 'unit',
)


def _is_megastore(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return "walmart" in host or "amazon" in host.split(".")


def _mega_should_skip_select(combined_lower: str, option_count: int) -> bool:
    """Drop obvious non-variant megastore dropdowns; keep size/color/style etc."""
    if any(s in combined_lower for s in _MEGA_EXTRA_SKIP_SUBSTRINGS):
        return True
    if option_count > 28 and not any(h in combined_lower for h in _VARIANT_DIM_HINTS):
        return True
    return False

# Pages that are not the actual PDP (bot walls, challenges, 404 dog pages, etc.)
_BLOCK_PAGE_SNIPPETS = (
    "robot or human",
    "verify you are human",
    "are you a human",
    "enter the characters you see below",
    "captcha",
    "automated access",
    "to discuss automated access",
    "sorry we couldn't find that page",
    "we couldnt find that page",
    "page not found",
    "access denied",
    # Retailer-specific soft blocks / edge pages
    "currently not available in your country",
    "please contact the site administrator",
    "oops!! something went wrong",
    "there was an error processing your request",
)


def _looks_blocked_html(url: str, html: str, title: str = "") -> Optional[str]:
    """Return a short reason if HTML looks like a challenge/blocked/non-PDP page."""
    t = (title or "").lower()
    h = (html or "").lower()

    # Cheap scan over a prefix (good enough for block pages)
    sample = (t + "\n" + h[:120_000])
    for snip in _BLOCK_PAGE_SNIPPETS:
        if snip in sample:
            return snip
    # Amazon-specific: their dog/error page often includes this id
    if "amazon" in urlparse(url).netloc.lower() and ("id=\"d\"" in h or "dogsofamazon" in h):
        return "amazon_error_page"
    return None


# JS snippet: returns True only if a buy control looks interactable (not loading shell / ghost).
_BUY_BUTTON_ENABLED_JS = """
() => {
    const SELECTORS = [
        '[id*="add-to-cart"]','[id*="addToCart"]','[id*="add_to_cart"]',
        '[data-action="add-to-cart"]','[data-testid*="add-to-cart"]',
        '[data-test*="add-to-cart"]','[data-automation-id*="add-to-cart"]',
        'button[name="add"]','[class*="AddToCart"]','[class*="add-to-cart"]',
        '[class*="atc-btn"]','[class*="AtcButton"]',
        '[data-hb-id*="AddToCart"]','[data-hb-id="LoadingButton"]',
        '[data-enzyme-id="AddToCart"]',
        '#buy-now-button','[id*="buy-now"]','[id*="buyNow"]',
        '[data-testid*="buy-now"]',
    ];
    const DISABLED_CLS = [
        'disabled','is-disabled','btn-disabled','button-disabled',
        'out-of-stock','sold-out','unavailable','inactive',
    ];
    const isUsable = (btn) => {
        if (btn.disabled) return false;
        if (btn.getAttribute('aria-disabled') === 'true') return false;
        if (btn.getAttribute('aria-busy') === 'true') return false;
        if (btn.offsetParent === null) return false;
        const cls = (btn.className || '').toLowerCase();
        if (DISABLED_CLS.some(c => cls.includes(c))) return false;
        try {
            const st = window.getComputedStyle(btn);
            if (st.pointerEvents === 'none') return false;
            if (parseFloat(st.opacity) < 0.15) return false;
            if (st.visibility === 'hidden' || st.display === 'none') return false;
        } catch (e) { /* ignore */ }
        const r = btn.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return false;
        return true;
    };
    for (const sel of SELECTORS) {
        for (const btn of document.querySelectorAll(sel)) {
            if (isUsable(btn)) return true;
        }
    }
    return false;
}
"""


async def _buy_button_enabled(page: Page) -> bool:
    """Return True if a buy button is currently enabled and visible on the live page."""
    try:
        return await page.evaluate(_BUY_BUTTON_ENABLED_JS)
    except Exception as e:
        logger.debug(f"JS buy-button check failed: {e}")
        return False


async def _buy_button_enabled_stable(page: Page, settle_ms: int = 280) -> bool:
    """Two-sample check to avoid transient 'flash' enabled states during SPA/hydration."""
    if not await _buy_button_enabled(page):
        return False
    await page.wait_for_timeout(settle_ms)
    return await _buy_button_enabled(page)


async def _discover_and_check_variants(page: Page, url: str) -> Dict[str, str]:
    """
    Discover product variant controls (selects, radios) and probe each option,
    checking whether the buy button is enabled after each selection.

    Megastores (Amazon, Walmart) use shorter waits and stricter <select> filtering
    so variant checking stays fast enough to finish within navigation budgets.
    """
    mega = _is_megastore(url)
    post_select_ms = 520 if mega else 1400
    max_variants = 30 if mega else 25
    max_options_per_select = 8 if mega else 12
    max_radio_groups = 3 if mega else 4
    max_radios_per_group = 10 if mega else 12

    results: Dict[str, str] = {}

    # ── SELECT DROPDOWNS ────────────────────────────────────────────────────
    try:
        select_els = await page.query_selector_all('select')
        for sel_el in select_els:
            if len(results) >= max_variants:
                break

            # Filter out non-variant selects by name/id
            name_attr = (await sel_el.get_attribute('name') or '').lower()
            id_attr   = (await sel_el.get_attribute('id')   or '').lower()
            combined  = name_attr + ' ' + id_attr
            if any(kw in combined for kw in _SKIP_SELECT_KEYWORDS):
                continue

            # Get options
            options_data = await page.evaluate(
                """(el) => Array.from(el.options)
                    .filter(o =>
                        o.value &&
                        o.value.trim() &&
                        !['', '0', 'false'].includes(o.value.trim()) &&
                        !o.text.match(/^(choose|select|pick|please select)/i)
                    )
                    .map(o => ({value: o.value, label: o.text.trim()}))
                """,
                sel_el,
            )

            if len(options_data) < 2:
                continue

            if mega and _mega_should_skip_select(combined, len(options_data)):
                logger.info(
                    f"Skipping non-product select '{name_attr or id_attr}' "
                    f"({len(options_data)} options) on megastore URL"
                )
                continue

            logger.info(f"Variant select '{name_attr or id_attr}': {len(options_data)} options")

            for opt in options_data[:max_options_per_select]:
                if len(results) >= max_variants:
                    break
                try:
                    await sel_el.select_option(value=opt['value'])
                    await page.wait_for_timeout(post_select_ms)
                    enabled = await _buy_button_enabled_stable(page)
                    results[opt['label']] = "available" if enabled else "unavailable"
                    logger.debug(f"  variant '{opt['label']}': {'✓' if enabled else '✗'}")
                except Exception as e:
                    logger.debug(f"  variant select error for '{opt['label']}': {e}")

    except Exception as e:
        logger.error(f"Select variant discovery error: {e}")

    # ── RADIO BUTTON GROUPS ─────────────────────────────────────────────────
    try:
        radio_groups = await page.evaluate(
            """
            (maxSlice) => {
                const groups = {};
                for (const r of document.querySelectorAll('input[type="radio"]')) {
                    const name = r.name || r.getAttribute('data-name') || '__unnamed__';
                    if (!groups[name]) groups[name] = [];
                    const label =
                        document.querySelector('label[for="' + r.id + '"]')?.textContent?.trim() ||
                        r.closest('label')?.textContent?.trim() ||
                        r.getAttribute('data-value') ||
                        r.value;
                    groups[name].push({value: r.value, label: label, id: r.id});
                }
                return Object.entries(groups)
                    .filter(([name, opts]) =>
                        opts.length > 1 &&
                        !/(qty|quantity|shipping|country|state|currency)/i.test(name)
                    )
                    .map(([name, opts]) => ({name, opts: opts.slice(0, maxSlice)}));
            }
            """,
            max_radios_per_group,
        )

        for group in radio_groups[:max_radio_groups]:
            if len(results) >= max_variants:
                break
            group_name = group['name']
            logger.info(f"Variant radio group '{group_name}': {len(group['opts'])} options")

            for opt in group['opts']:
                if len(results) >= max_variants:
                    break
                label = opt['label'] or opt['value']
                try:
                    # Prefer ID-based selector for precision
                    if opt.get('id'):
                        radio = await page.query_selector(f'#{opt["id"]}')
                    else:
                        radio = await page.query_selector(
                            f'input[type="radio"][name="{group_name}"][value="{opt["value"]}"]'
                        )
                    if radio:
                        await radio.click()
                        await page.wait_for_timeout(post_select_ms)
                        enabled = await _buy_button_enabled_stable(page)
                        results[label] = "available" if enabled else "unavailable"
                        logger.debug(f"  radio '{label}': {'✓' if enabled else '✗'}")
                except Exception as e:
                    logger.debug(f"  radio error for '{label}': {e}")

    except Exception as e:
        logger.error(f"Radio variant discovery error: {e}")

    # ── ARIA LISTBOX VARIANTS (custom dropdowns) ────────────────────────────
    # Some retailers render variants as <div role="listbox"> with <div role="option">.
    # Probe a small number of options to keep the scan bounded.
    try:
        listboxes = await page.query_selector_all('[role="listbox"]')
        # Keep it small; if we already found variants via select/radio, just do a quick pass.
        max_listboxes = 2 if results else (1 if mega else 3)
        max_options_per_listbox = 8 if mega else 10

        for lb in listboxes[:max_listboxes]:
            if len(results) >= max_variants:
                break
            try:
                options = await lb.query_selector_all('[role="option"]')
            except Exception:
                options = []
            if len(options) < 2:
                continue

            for opt in options[:max_options_per_listbox]:
                if len(results) >= max_variants:
                    break
                try:
                    label = (await opt.inner_text()) or ""
                    label = " ".join(label.split()).strip()
                    if not label:
                        # fall back to aria-label
                        label = (await opt.get_attribute("aria-label")) or ""
                        label = " ".join(label.split()).strip()
                    if not label:
                        continue

                    await opt.click()
                    await page.wait_for_timeout(post_select_ms)
                    enabled = await _buy_button_enabled_stable(page)
                    # Avoid overwriting a more specific label discovered earlier
                    if label not in results:
                        results[label] = "available" if enabled else "unavailable"
                except Exception as e:
                    logger.debug(f"  listbox option click error: {e}")
    except Exception as e:
        logger.error(f"Listbox variant discovery error: {e}")

    return results


async def _playwright_scrape(url: str) -> Tuple[Optional[str], Dict[str, str], Optional[bool]]:
    """
    Full Playwright scrape: navigate, get HTML, then check all variants.
    Returns (html_content, variant_results).
    variant_results is {} when no variants found or variant checking disabled.
    """
    browser = None
    context = None
    page = None
    mega = _is_megastore(url)
    host = urlparse(url).netloc.lower()
    # Megastores: long nav budget (slow bot walls + heavy PDP JS)
    nav_timeout_ms = int(TIMEOUT * 1000 * (5 if mega else 1))
    async def _run(use_scrapingbee_proxy: bool) -> Tuple[Optional[str], Dict[str, str], Optional[bool]]:
        nonlocal browser, context, page
        async with async_playwright() as p:
            launch_kwargs = {
                "headless": HEADLESS,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            }
            if use_scrapingbee_proxy and SCRAPINGBEE_API_KEY:
                # ScrapingBee proxy-mode: route requests through their rotating proxy pool.
                # Playwright runs JS locally; keep render_js disabled to avoid extra credits.
                launch_kwargs["proxy"] = {
                    "server": "http://proxy.scrapingbee.com:8886",
                    "username": SCRAPINGBEE_API_KEY,
                    "password": f"render_js=False&premium_proxy=True&stealth_proxy=True&country_code={SCRAPINGBEE_COUNTRY}",
                }

            try:
                # Some sites intermittently fail in Chromium with net::ERR_HTTP2_PROTOCOL_ERROR.
                # Use Firefox for better reliability on those domains.
                use_firefox = any(d in host for d in ("staples.com", "officedepot.com"))
                if use_firefox:
                    ff_kwargs = {"headless": HEADLESS}
                    if use_scrapingbee_proxy and SCRAPINGBEE_API_KEY:
                        ff_kwargs["proxy"] = launch_kwargs.get("proxy")
                    browser = await p.firefox.launch(**ff_kwargs)
                else:
                    browser = await p.chromium.launch(**launch_kwargs)
            except Exception as launch_err:
                if ("Executable doesn't exist" in str(launch_err) or 'playwright install' in str(launch_err).lower()):
                    logger.error("Playwright browser not installed. Run: playwright install chromium")
                raise

            state_path = _storage_state_path_for(url)
            context_kwargs = dict(
                user_agent=USER_AGENT,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                ignore_https_errors=bool(use_scrapingbee_proxy),
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            if state_path.exists():
                context_kwargs["storage_state"] = str(state_path)

            context = await browser.new_context(**context_kwargs)

            stealth = Stealth()
            for script in stealth.enabled_scripts:
                await context.add_init_script(script)

            page = await context.new_page()
            try:
                async def _route_handler(route):
                    try:
                        rt = route.request.resource_type
                        if rt in {"image", "media", "font"}:
                            return await route.abort()
                        return await route.continue_()
                    except Exception:
                        return await route.continue_()
                await page.route("**/*", _route_handler)
            except Exception:
                pass
            logger.info(f"Playwright navigating to {url}{' (via ScrapingBee proxy)' if use_scrapingbee_proxy else ''}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=nav_timeout_ms)
            except Exception:
                # Best-effort screenshot on navigation error
                shot = _screenshot_path_for(url, "goto_error")
                if shot is not None:
                    try:
                        await page.screenshot(path=str(shot), full_page=False)
                    except Exception:
                        pass
                raise

            # Wait for buy button (specific to avoid "Add to wishlist" false-match)
            btn_wait = 8000 if mega else 5000
            try:
                host_for_wait = urlparse(url).netloc.lower()
                if any(d in host_for_wait for d in ("kohls.com", "lowes.com", "officedepot.com", "overstock.com", "staples.com")):
                    # These retailers can hydrate the CTA after DOMContentLoaded.
                    # Do a best-effort wait on common ATC hooks before taking the HTML snapshot.
                    try:
                        await page.wait_for_selector(
                            '[data-testid*="add-to-cart"], [data-test*="add-to-cart"], '
                            'button[id*="add-to-cart"], button[id*="addToCart"], '
                            '#add-to-cart, #add-to-cart-button, '
                            'button:has-text("Add to Cart"), button:has-text("Add to Bag")',
                            timeout=btn_wait,
                            state="visible",
                        )
                        await page.wait_for_timeout(750)
                    except Exception:
                        pass
                await page.wait_for_selector(
                    'button:has-text("Add to Cart"), button:has-text("Add to cart"), '
                    'button:has-text("Add to Bag"), button:has-text("Add to bag"), '
                    '[id*="add-to-cart"], [data-action="add-to-cart"], '
                    '[data-automation-id="atc"], [data-automation-id="add-to-cart-button"]',
                    timeout=btn_wait,
                    state='visible'
                )
                await page.wait_for_timeout(1500 if mega else 1000)
            except Exception:
                await page.wait_for_timeout(4000 if mega else 3000)

            html_content = await page.content()
            # Live DOM vs HTML: capture before variant clicks (matches soup snapshot).
            live_buy_at_html = await _buy_button_enabled_stable(page)

            # If we hit a bot wall / challenge / non-PDP, stop early so the caller can fall back.
            try:
                title = await page.title()
            except Exception:
                title = ""
            block_reason = _looks_blocked_html(url, html_content or "", title)
            if block_reason:
                shot = _screenshot_path_for(url, f"blocked_{block_reason}")
                if shot is not None:
                    try:
                        await page.screenshot(path=str(shot), full_page=False)
                    except Exception:
                        pass
                logger.warning(f"Playwright blocked/challenge page for {url}: {block_reason}")
                return None, {}, live_buy_at_html

            # Variant checking — only when Playwright is available (needs live DOM)
            variant_results: Dict[str, str] = {}
            if CHECK_VARIANTS:
                logger.info(f"Checking variants for {url}")
                variant_budget_s = 30 if mega else 45
                try:
                    variant_results = await asyncio.wait_for(
                        _discover_and_check_variants(page, url),
                        timeout=variant_budget_s,
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Variant checking timed out after {variant_budget_s}s for {url} — continuing without variants")
                    variant_results = {}
                if variant_results:
                    available_count = sum(1 for v in variant_results.values() if v == "available")
                    logger.info(
                        f"Variants for {url}: {available_count}/{len(variant_results)} available — "
                        + ", ".join(f"{k}={v}" for k, v in list(variant_results.items())[:5])
                    )
                else:
                    logger.info(f"No variants detected for {url}")

            await page.close()
            await context.close()
            await browser.close()
            return html_content, variant_results, live_buy_at_html

    try:
        async with _playwright_semaphore:
            html_content, variant_results, live_buy_at_html = await _run(use_scrapingbee_proxy=False)

            # If we're blocked/edge-paged, retry once with a fresh context (ignore storage_state)
            if html_content is None:
                try:
                    fresh = os.environ.get("SCRAPER_RETRY_FRESH_CONTEXT", "true").lower() in ("1", "true", "yes")
                    if fresh:
                        # Temporarily move aside any storage_state file for this call.
                        st = _storage_state_path_for(url)
                        tmp = st.with_suffix(st.suffix + ".bak_temp_retry")
                        moved = False
                        if st.exists():
                            try:
                                st.replace(tmp)
                                moved = True
                            except Exception:
                                moved = False
                        try:
                            html_content, variant_results, live_buy_at_html = await _run(use_scrapingbee_proxy=False)
                        finally:
                            if moved and tmp.exists() and not st.exists():
                                try:
                                    tmp.replace(st)
                                except Exception:
                                    pass
                except Exception:
                    pass

            # If we're blocked on tough sites, retry once through ScrapingBee proxy-mode.
            if (html_content is None) and ("walmart" in urlparse(url).netloc.lower() or "target" in urlparse(url).netloc.lower()):
                if SCRAPINGBEE_API_KEY:
                    html_content, variant_results, live_buy_at_html = await _run(use_scrapingbee_proxy=True)
            return html_content, variant_results, live_buy_at_html

    except PlaywrightTimeout:
        logger.error(f"Playwright timeout for {url} after {nav_timeout_ms / 1000:.0f}s")
    except Exception as e:
        logger.error(f"Playwright error for {url}: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        for obj, name in [(page, 'page'), (context, 'context'), (browser, 'browser')]:
            if obj:
                try:
                    await obj.close()
                except Exception as cleanup_err:
                    logger.warning(f"Cleanup error ({name}): {cleanup_err}")
    return None, {}, None


async def fetch_scrapingbee_html(url: str) -> Optional[str]:
    """Fetch via ScrapingBee API — residential proxies + JS rendering."""
    if not SCRAPINGBEE_API_KEY:
        return None
    try:
        host = urlparse(url).netloc.lower()
        tough = ("walmart" in host) or ("target" in host)
        await _scrapingbee_rate_limit_wait()
        from scrapingbee import ScrapingBeeClient
        client = ScrapingBeeClient(api_key=SCRAPINGBEE_API_KEY)
        loop = asyncio.get_event_loop()
        async with _scrapingbee_semaphore:
            # ScrapingBee SDK ultimately uses requests; enforce an asyncio-level timeout
            # so a hung request doesn't stall the whole scan/benchmark.
            base_params = {
                'premium_proxy': True,
                # Tough anti-bot sites often need the stealth pool + more time to hydrate.
                **({'stealth_proxy': True} if tough else {}),
                'country_code': SCRAPINGBEE_COUNTRY,
                # Better debugging: return the target's real HTTP status code.
                'transparent_status_code': True,
                # Forward our headers (UA/lang) to the target page.
                'forward_headers': True,
                # Sticky IP for a few minutes can help some bot defenses.
                **({'session_id': random.randint(0, 10_000_000)} if tough else {}),
            }
            headers = {
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            def _do(params: dict):
                return client.get(url, params=params, headers=headers)

            # First try: JS render (needed for most PDPs)
            params_js = {
                **base_params,
                'render_js': True,
                'wait': 8000 if tough else 3500,
                # Tough sites can crash with heavy assets; block for stability.
                'block_resources': True if tough else False,
                **({'wait_browser': 'domcontentloaded'} if tough else {}),
            }
            response = await asyncio.wait_for(
                loop.run_in_executor(_bee_executor, lambda: _do(params_js)),
                timeout=max(15, int(TIMEOUT) * 3),
            )

            # Some tough sites intermittently 5xx on JS rendering; retry without JS as a fallback.
            if tough and int(getattr(response, "status_code", 0) or 0) >= 500:
                params_nojs = {
                    **base_params,
                    'render_js': False,
                    'wait': 0,
                    'block_resources': True,
                }
                response = await asyncio.wait_for(
                    loop.run_in_executor(_bee_executor, lambda: _do(params_nojs)),
                    timeout=max(15, int(TIMEOUT) * 3),
                )
        if response.status_code == 200:
            logger.info(f"ScrapingBee OK {len(response.text)} chars for {url}")
            return response.text

        # Some sites return HTML with non-200 status (soft blocks / disguised 404s).
        # If we got substantial HTML, return it so downstream block-page detection and
        # button detection can decide what to do.
        try:
            body = getattr(response, "text", None)
            if isinstance(body, str) and len(body) >= 20_000:
                logger.warning(
                    f"ScrapingBee non-200 but HTML present "
                    f"(status={response.status_code} len={len(body)}) for {url}"
                )
                return body
        except Exception:
            body = None

        if response.status_code == 401:
            logger.error("ScrapingBee: invalid API key (401)")
        elif response.status_code == 402:
            logger.error("ScrapingBee: credit quota exhausted (402) — falling back")
        elif response.status_code == 429:
            logger.warning("ScrapingBee: rate limited (429) — falling back")
        else:
            logger.warning(f"ScrapingBee HTTP {response.status_code} for {url}")
        return None
    except asyncio.TimeoutError:
        logger.warning(f"ScrapingBee timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"ScrapingBee error for {url}: {type(e).__name__}: {e}")
        return None


async def fetch_static_html(url: str, session: aiohttp.ClientSession) -> Optional[str]:
    """Last-resort static HTTP fetch via aiohttp."""
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
        async with session.get(
            url, headers=headers,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT),
            allow_redirects=True,
            # Some networks inject a MITM certificate (common on corporate Wi-Fi).
            # Keep verification on by default; allow override via env for local testing.
            ssl=SCRAPER_STATIC_SSL_VERIFY,
        ) as response:
            if response.status == 200:
                return await response.text()
            logger.warning(f"Static HTTP {response.status} for {url}")
            return None
    except asyncio.TimeoutError:
        logger.error(f"Static timeout for {url}")
        return None
    except Exception as e:
        logger.error(f"Static error for {url}: {type(e).__name__}: {e}")
        return None


async def scrape_url(url: str, use_playwright: bool = True) -> Dict:
    """
    Scrape URL, detect buy buttons, and check all product variants.

    Fetch order: Playwright first by default (scraper_scrapingbee_first=False).
    Set scrape_method / html_primary_source for debugging (first HTML vs final row).
    Variant results only when Playwright supplies HTML.
    """
    start_time = time.time()
    result: Dict = {
        "url": url,
        "scanned_at": datetime.utcnow(),
        "add_to_cart": False,
        "buy_now": False,
        "status": "error",
        "error_message": None,
        "response_time": None,
        "scrape_method": None,
        "html_primary_source": None,
        "blocked_reason": None,
        "variants": {},           # {label: "available"|"unavailable"}
        "variants_checked": False,
    }

    def _mark_first_html(source: str, method: str) -> None:
        if result.get("html_primary_source") is None:
            result["html_primary_source"] = source
        result["scrape_method"] = method

    try:
        logger.info(f"Scraping {url} (scrapingbee_first={SCRAPER_SCRAPINGBEE_FIRST})")
        html_content = None
        variant_results: Dict[str, str] = {}
        live_buy_at_html: Optional[bool] = None

        async def _try_playwright() -> None:
            nonlocal html_content, variant_results, live_buy_at_html
            if not use_playwright:
                return
            try:
                h, vr, live = await _playwright_scrape(url)
                if h:
                    html_content = h
                    variant_results = vr
                    live_buy_at_html = live
                    _mark_first_html("playwright", "playwright")
                    result["variants"] = variant_results
                    result["variants_checked"] = bool(variant_results) or CHECK_VARIANTS
            except Exception as e:
                logger.error(f"Playwright failed for {url}: {e}")

        async def _try_scrapingbee() -> None:
            nonlocal html_content, variant_results, live_buy_at_html
            if not SCRAPINGBEE_API_KEY:
                return
            h = await fetch_scrapingbee_html(url)
            if h and _looks_blocked_html(url, h):
                logger.warning(f"ScrapingBee blocked/challenge HTML for {url}")
                return
            if h:
                html_content = h
                variant_results = {}
                live_buy_at_html = None
                _mark_first_html("scrapingbee", "scrapingbee")
                result["variants"] = {}
                result["variants_checked"] = False

        if SCRAPER_SCRAPINGBEE_FIRST:
            await _try_scrapingbee()
            if not html_content:
                await _try_playwright()
        else:
            await _try_playwright()
            if not html_content:
                await _try_scrapingbee()

        # Static HTTP fallback (no variant support)
        if not html_content:
            try:
                async with aiohttp.ClientSession() as session:
                    html_content = await fetch_static_html(url, session)
                if html_content:
                    if _looks_blocked_html(url, html_content):
                        logger.warning(f"Static HTTP returned blocked/challenge HTML for {url}")
                        html_content = None
                    else:
                        _mark_first_html("static", "static")
            except Exception as e:
                logger.error(f"Static fetch failed for {url}: {e}")

        if not html_content:
            result["error_message"] = "All fetch methods failed (ScrapingBee, Playwright, static HTTP)"
            result["status"] = "error"
            return result

        blocked = _looks_blocked_html(url, html_content)
        if blocked:
            result["blocked_reason"] = blocked
            result["error_message"] = f"blocked:{blocked}"
            result["status"] = "error"
            return result

        # HTML-based detection (always run — used for ScrapingBee and static results)
        detection = detector.detect_all_buttons(html_content, url)

        # Determine final availability:
        # If variants were found via Playwright, they take precedence over HTML detection.
        # A product is "available" if ANY variant is purchasable.
        if variant_results:
            any_available = any(v == "available" for v in variant_results.values())
            # Strong in-scope OOS copy beats a flaky single-variant "available" flash.
            if detection.get("unavailability_override"):
                any_available = False
            result.update({
                "add_to_cart": any_available,
                "buy_now": detection["buy_now"] if any_available else False,
                "status": "available" if any_available else "unavailable",
                "error_message": None,
                "unavailability_override": detection.get("unavailability_override", False),
            })
        else:
            result.update({
                "add_to_cart": detection["add_to_cart"],
                "buy_now": detection["buy_now"],
                "status": detection["status"],
                "error_message": None,
                "unavailability_override": detection.get("unavailability_override", False),
            })
            # HTML can show a stale/loading ATC (common on Wayfair); trust live Chromium if it disagrees.
            if (
                live_buy_at_html is not None
                and result.get("scrape_method") == "playwright"
                and not variant_results
            ):
                if live_buy_at_html is False and (result["add_to_cart"] or result["buy_now"]):
                    result["add_to_cart"] = False
                    result["buy_now"] = False
                    result["status"] = "unavailable"
                    logger.info(f"Live DOM: no usable buy control — overriding HTML detection for {url}")

        # ScrapingBee HTML is often ahead/behind the real PDP; Wayfair especially — confirm with Playwright.
        if (
            result.get("scrape_method") == "scrapingbee"
            and use_playwright
            and "wayfair.com" in url.lower()
            and result.get("status") == "available"
            and (result.get("add_to_cart") or result.get("buy_now"))
        ):
            try:
                html2, var2, live2 = await _playwright_scrape(url)
                if html2:
                    det2 = detector.detect_all_buttons(html2, url)
                    html_ok = bool(det2.get("add_to_cart") or det2.get("buy_now"))
                    live_ok = live2 is True
                    if not live_ok and not html_ok:
                        result["add_to_cart"] = False
                        result["buy_now"] = False
                        result["status"] = "unavailable"
                        result["variants"] = var2 or {}
                        result["variants_checked"] = bool(var2) or CHECK_VARIANTS
                        result["scrape_method"] = "playwright"
                        result["unavailability_override"] = det2.get("unavailability_override", False)
                    elif not live_ok and html_ok:
                        result["add_to_cart"] = False
                        result["buy_now"] = bool(det2.get("buy_now"))
                        result["status"] = "available" if result["buy_now"] else "unavailable"
                        result["variants"] = var2 or {}
                        result["variants_checked"] = bool(var2) or CHECK_VARIANTS
                        result["scrape_method"] = "playwright"
                        result["unavailability_override"] = det2.get("unavailability_override", False)
                    else:
                        result["variants"] = var2 or result.get("variants") or {}
                        result["variants_checked"] = bool(var2) or CHECK_VARIANTS
                        result["scrape_method"] = "playwright"
            except Exception as e:
                logger.warning(f"Wayfair Playwright verify pass failed: {e}")

        logger.info(
            f"Done {url}: status={result['status']} "
            f"html_primary={result.get('html_primary_source')} "
            f"final_method={result['scrape_method']} "
            f"variants={len(variant_results)} "
            f"atc={result['add_to_cart']} bn={result['buy_now']}"
        )

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        result["error_message"] = str(e)
        result["status"] = "error"

    finally:
        result["response_time"] = round(time.time() - start_time, 2)

    return result


async def scrape_multiple_urls(urls: list, use_playwright: bool = True, max_concurrent: int = 3) -> list:
    """Scrape multiple URLs with bounded concurrency.
    Default max_concurrent=3 because variant checking is slow per URL.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded(url):
        async with semaphore:
            return await scrape_url(url, use_playwright)

    return list(await asyncio.gather(*[bounded(u) for u in urls]))


async def test_scraper():
    test_urls = ["https://www.example.com"]
    for url in test_urls:
        print(f"\n{'='*60}\nTesting: {url}\n{'='*60}")
        r = await scrape_url(url)
        print(f"Status:      {r['status']}")
        print(f"Add to Cart: {r['add_to_cart']}")
        print(f"Buy Now:     {r['buy_now']}")
        print(f"Method:      {r['scrape_method']}")
        print(f"Variants:    {r['variants']}")
        print(f"Time:        {r['response_time']}s")
        if r['error_message']:
            print(f"Error:       {r['error_message']}")


if __name__ == "__main__":
    asyncio.run(test_scraper())
