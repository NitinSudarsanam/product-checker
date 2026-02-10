import json
import logging
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

# Text on page that overrides button detection — product is unavailable
_UNAVAILABLE_SIGNALS = [
    "sold out",
    "out of stock",
    "currently unavailable",
    "item unavailable",
    "not available",
    "temporarily out of stock",
    "back order",
    "backordered",
    "notify me when available",
    "join waitlist",
    "join the waitlist",
    "out-of-stock",
]

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
        # CSS class names
        classes = set(c.lower() for c in element.get('class', []))
        if classes & _DISABLED_CLASSES:
            return False
        # data attributes some sites use
        if element.get('data-disabled') in ('true', '1'):
            return False
        return True

    def _has_unavailability_signal(self, soup: BeautifulSoup) -> bool:
        """Check if page contains explicit out-of-stock / sold-out text.

        Used as a final override: if page clearly says "sold out", report
        unavailable even if a (stale) buy button DOM node still exists.
        """
        # Look in common containers first (faster + more accurate than full text)
        containers = (
            soup.find_all(class_=lambda c: c and any(
                kw in ' '.join(c).lower()
                for kw in ('availability', 'stock', 'status', 'inventory', 'atc', 'pdp')
            ))
            or [soup]  # fall back to full page
        )
        for container in containers:
            text = self._normalize_text(container.get_text(' ', strip=True))
            for signal in _UNAVAILABLE_SIGNALS:
                if signal in text:
                    logger.debug(f"Unavailability signal found: '{signal}'")
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
        unavailability_override = button_found and self._has_unavailability_signal(soup)
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
