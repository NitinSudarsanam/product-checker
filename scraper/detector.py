import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_FALLBACK_RULES = {
    "settings": {"case_sensitive": False, "partial_match": True},
    "add_to_cart": {
        "text_patterns": ["add to cart", "add to bag", "add to basket"],
        "css_selectors": [
            "[id*='add-to-cart']", "[class*='add-to-cart']",
            "[id*='addToCart']", "[class*='addToCart']",
        ],
    },
    "buy_now": {
        "text_patterns": ["buy now", "buy it now", "purchase now"],
        "css_selectors": [
            "[id*='buy-now']", "[class*='buy-now']",
            "[id*='buyNow']", "[class*='buyNow']",
        ],
    },
}

# Text on page that overrides button detection — product is unavailable.
# Keep phrases specific; vague strings like "not available" match unrelated
# PDP copy (fulfillment, other sellers, recommendations) and false-negative Walmart/Amazon.
_UNAVAILABLE_SIGNALS = [
    "sold out",
    "out of stock",
    "currently unavailable",
    "item unavailable",
    "temporarily out of stock",
    "back order",
    "backordered",
    "notify me when available",
    "join waitlist",
    "join the waitlist",
    "out-of-stock",
    "we don't know when or if this item will be back in stock",
    "this item cannot be shipped to your selected delivery location",
    "no longer available",
    "has been discontinued",
    "discontinued by manufacturer",
    "notify me",
]

# Text that often appears on OOS CTAs but is not a purchase action
_NEGATIVE_BUY_TEXT = (
    "notify me",
    "notify",
    "email me",
    "join waitlist",
    "waitlist",
    "out of stock",
    "sold out",
)

# CSS classes/attrs that mark a button as non-functional even if text matches
_DISABLED_CLASSES = {
    'disabled', 'is-disabled', 'btn-disabled', 'button-disabled',
    'out-of-stock', 'sold-out', 'unavailable', 'inactive',
    'not-available', 'oos', 'outofstock',
}


class ButtonDetector:

    def __init__(self, rules_file: str = "detection_rules.json"):
        rules_path = Path(__file__).parent / rules_file
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
            logger.info(f"Detection rules loaded from {rules_path}")
        except FileNotFoundError:
            logger.error(f"Rules file not found: {rules_path}. Using fallback.")
            self.rules = _FALLBACK_RULES
        except json.JSONDecodeError as e:
            logger.error(f"Rules JSON malformed: {e}. Using fallback.")
            self.rules = _FALLBACK_RULES
        except Exception as e:
            logger.error(f"Failed to load rules: {e}. Using fallback.")
            self.rules = _FALLBACK_RULES

        self.settings = self.rules.get("settings", {})
        self.case_sensitive = self.settings.get("case_sensitive", False)
        self.partial_match = self.settings.get("partial_match", True)

    def _get_domain(self, url: str) -> str:
        try:
            return urlparse(url).netloc.replace('www.', '')
        except Exception:
            return ""

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = ' '.join(text.split())  # collapse whitespace
        return text if self.case_sensitive else text.lower()

    def _is_button_enabled(self, element: Tag) -> bool:
        """Return False if element is visually/semantically disabled.

        Checks HTML disabled attr, aria-disabled, and common disabled CSS classes.
        A disabled button present on page should NOT count as available.
        """
        # HTML disabled attribute
        if element.get('disabled') is not None:
            return False
        # ARIA disabled
        if element.get('aria-disabled') in ('true', '1'):
            return False
        # Still hydrating / not actionable (Wayfair, React SPAs)
        if element.get('aria-busy') in ('true', '1'):
            return False
        # CSS class names
        classes = set(c.lower() for c in element.get('class', []))
        if classes & _DISABLED_CLASSES:
            return False
        # data attributes some sites use
        if element.get('data-disabled') in ('true', '1'):
            return False
        # OOS CTA text should not count as a buy button even if it's clickable
        try:
            txt = self._normalize_text(element.get_text(" ", strip=True))
            aria = self._normalize_text(element.get("aria-label", "") or "")
            title = self._normalize_text(element.get("title", "") or "")
            combined = " ".join([txt, aria, title])
            if any(bad in combined for bad in _NEGATIVE_BUY_TEXT):
                return False
        except Exception:
            pass
        return True

    def _product_scope_elements(self, soup: BeautifulSoup, url: str) -> List[Tag]:
        """Narrow regions where OOS copy is trustworthy (avoid recs / footer / other sellers)."""
        domain = self._get_domain(url)
        regions: List[Tag] = []
        seen = set()

        def add_el(el: Optional[Tag]) -> None:
            if el is None or id(el) in seen:
                return
            seen.add(id(el))
            regions.append(el)

        # High-signal layout hooks (order matters)
        for sel in (
            "#buybox",
            "#dp",
            "#centerCol",
            "#ppd",
            '[data-testid="product-buy-box"]',
            '[data-testid="add-to-cart-section"]',
            "main",
            '[role="main"]',
            "#main-content",
            "#main",
            "[itemprop='offers']",
            "[itemprop=\"offers\"]",
        ):
            try:
                for el in soup.select(sel):
                    add_el(el)
            except Exception:
                continue

        # Retailer-specific hooks
        if "walmart.com" in domain:
            for sel in ('[data-testid="product"]', "#main", "article"):
                try:
                    for el in soup.select(sel):
                        add_el(el)
                except Exception:
                    continue

        if "wayfair.com" in domain:
            for sel in ("#pdp-mt-grid", "#pdp", "article"):
                try:
                    for el in soup.select(sel):
                        add_el(el)
                except Exception:
                    continue

        if re.search(r"(^|\.)amazon\.", domain):
            for sel in ("#ppd", "#desktop_buybox", "#mobile_buybox", "#freshBuyBox"):
                try:
                    for el in soup.select(sel):
                        add_el(el)
                except Exception:
                    continue

        if not regions:

            def _class_text(c) -> str:
                if isinstance(c, list):
                    return " ".join(c).lower()
                return str(c).lower()

            for el in soup.find_all(class_=lambda c: c and any(
                kw in _class_text(c)
                for kw in ("availability", "inventory", "fulfillment-atc", "add-to-cart")
            )):
                add_el(el)

        return regions

    @staticmethod
    def _out_of_stock_is_product_level(text: str) -> bool:
        """True if an 'out of stock' mention is likely this SKU, not 'other sellers' / compare."""
        t = text.lower()
        start = 0
        phrase = "out of stock"
        while True:
            j = t.find(phrase, start)
            if j < 0:
                return False
            window = t[j : j + 80]
            if "other seller" in window or "from other" in window or "compare with" in window:
                start = j + len(phrase)
                continue
            return True

    def _has_unavailability_signal(self, soup: BeautifulSoup, url: str) -> bool:
        """True only if explicit OOS phrases appear inside product-scoped regions.

        Never scans the full document: related products and global nav often contain
        'out of stock' / 'unavailable' and would incorrectly kill a valid PDP buy button.
        """
        containers = self._product_scope_elements(soup, url)
        if not containers:
            # Wayfair uses heavily hashed classes; product scoping can fail.
            domain = self._get_domain(url)
            if "wayfair.com" in domain:
                raw = str(soup).lower()
                sample = raw[:120000] + " " + raw[-120000:]
                if ("out of stock" in sample) or ("notify me" in sample):
                    return True
            return False

        for container in containers:
            text = self._normalize_text(container.get_text(" ", strip=True))
            # Large pages (Wayfair) can place OOS copy far from the top.
            # Sample both head and tail to avoid missing in-scope signals.
            if len(text) > 80000:
                text = text[:80000] + " " + text[-80000:]
            for signal in _UNAVAILABLE_SIGNALS:
                if signal in text:
                    if signal == "out of stock" and not self._out_of_stock_is_product_level(text):
                        continue
                    logger.debug(f"Unavailability signal found in product scope: '{signal}'")
                    return True
        # Wayfair: if we scoped but missed text extraction, fall back to raw HTML sample.
        domain = self._get_domain(url)
        if "wayfair.com" in domain:
            raw = str(soup).lower()
            if ("out of stock" in raw) or ("notify me" in raw):
                return True
        return False

    def _check_text_match(self, element_text: str, patterns: List[str]) -> bool:
        element_text = self._normalize_text(element_text)
        for pattern in patterns:
            p = self._normalize_text(pattern)
            if self.partial_match:
                if p in element_text:
                    return True
            else:
                if p == element_text:
                    return True
        return False

    def _get_button_candidates(self, soup: BeautifulSoup) -> List[Tag]:
        """Collect all elements that could be buy buttons."""
        candidates: List[Tag] = list(soup.find_all(['button', 'a', 'input']))
        # div/span acting as buttons
        for tag in soup.find_all(['div', 'span']):
            role = tag.get('role', '')
            cls = ' '.join(tag.get('class', []))
            if role == 'button' or 'btn' in cls.lower() or 'button' in cls.lower():
                candidates.append(tag)
        return candidates

    def _check_selector_enabled(self, soup: BeautifulSoup, selectors: List[str]) -> bool:
        """Return True if any selector matches an ENABLED element."""
        for selector in selectors:
            try:
                for el in soup.select(selector):
                    if self._is_button_enabled(el):
                        return True
            except Exception:
                continue
        return False

    def _check_text_patterns(self, soup: BeautifulSoup, patterns: List[str]) -> bool:
        """Return True if any ENABLED element's text/attr matches a pattern."""
        for element in self._get_button_candidates(soup):
            if not self._is_button_enabled(element):
                continue
            text = element.get_text(strip=True)
            if self._check_text_match(text, patterns):
                return True
            for attr in ['value', 'title', 'aria-label', 'data-text']:
                val = element.get(attr, '')
                if val and self._check_text_match(val, patterns):
                    return True
        return False

    def _parse_html(self, html_content: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html_content, 'lxml')
        except Exception:
            logger.warning("lxml unavailable, falling back to html.parser")
            return BeautifulSoup(html_content, 'html.parser')

    def detect_button(self, html_content: str, url: str, button_type: str) -> Tuple[bool, str]:
        try:
            soup = self._parse_html(html_content)
            domain = self._get_domain(url)
            button_rules = self.rules.get(button_type, {})

            # 1. Domain-specific rules
            for domain_pattern, rules in button_rules.get("domains", {}).items():
                if domain_pattern in domain:
                    if "selectors" in rules and self._check_selector_enabled(soup, rules["selectors"]):
                        return True, f"domain_selector_{domain_pattern}"
                    if "text" in rules and self._check_text_patterns(soup, rules["text"]):
                        return True, f"domain_text_{domain_pattern}"

            # 2. Generic CSS selectors
            if self._check_selector_enabled(soup, button_rules.get("css_selectors", [])):
                return True, "css_selector"

            # 3. Generic text patterns
            if self._check_text_patterns(soup, button_rules.get("text_patterns", [])):
                return True, "text_pattern"

            return False, "not_found"

        except Exception as e:
            logger.error(f"Detection error for {url}: {e}")
            return False, f"error: {str(e)}"

    def detect_all_buttons(self, html_content: str, url: str) -> Dict:
        soup = self._parse_html(html_content)

        add_to_cart_found, add_to_cart_method = self.detect_button(html_content, url, "add_to_cart")
        buy_now_found, buy_now_method = self.detect_button(html_content, url, "buy_now")

        button_found = add_to_cart_found or buy_now_found

        # Override: explicit sold-out / out-of-stock signal on page beats button detection.
        # Handles variant pages where default is OOS but button DOM still renders.
        unavailability_override = button_found and self._has_unavailability_signal(soup, url)
        if unavailability_override:
            logger.info(f"Unavailability override for {url} — button found but OOS signal detected")
            add_to_cart_found = False
            buy_now_found = False
            add_to_cart_method = "overridden_by_oos_signal"
            buy_now_method = "overridden_by_oos_signal"

        return {
            "add_to_cart": add_to_cart_found,
            "add_to_cart_method": add_to_cart_method,
            "buy_now": buy_now_found,
            "buy_now_method": buy_now_method,
            "status": "available" if (add_to_cart_found or buy_now_found) else "unavailable",
            "unavailability_override": unavailability_override,
        }


detector = ButtonDetector()
