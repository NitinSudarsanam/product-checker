import json
from pathlib import Path
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re


class ButtonDetector:
    """Detect buy buttons using configurable rules"""
    
    def __init__(self, rules_file: str = "detection_rules.json"):
        """Initialize detector with rules"""
        rules_path = Path(__file__).parent / rules_file
        with open(rules_path, 'r', encoding='utf-8') as f:
            self.rules = json.load(f)
        
        self.settings = self.rules.get("settings", {})
        self.case_sensitive = self.settings.get("case_sensitive", False)
        self.partial_match = self.settings.get("partial_match", True)
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return ""
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        text = text.strip()
        if not self.case_sensitive:
            text = text.lower()
        return text
    
    def _check_text_match(self, element_text: str, patterns: List[str]) -> bool:
        """Check if element text matches any pattern"""
        element_text = self._normalize_text(element_text)
        
        for pattern in patterns:
            pattern = self._normalize_text(pattern)
            
            if self.partial_match:
                if pattern in element_text:
                    return True
            else:
                if pattern == element_text:
                    return True
        
        return False
    
    def _check_selector(self, soup: BeautifulSoup, selectors: List[str]) -> bool:
        """Check if any selector matches an element"""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    return True
            except Exception:
                continue
        return False
    
    def _check_text_patterns(self, soup: BeautifulSoup, patterns: List[str]) -> bool:
        """Check if any text pattern is found in buttons"""
        # Check all button elements
        buttons = soup.find_all(['button', 'a', 'input'])
        
        for button in buttons:
            # Check button text
            button_text = button.get_text(strip=True)
            if self._check_text_match(button_text, patterns):
                return True
            
            # Check button attributes
            for attr in ['value', 'title', 'aria-label', 'data-text']:
                attr_value = button.get(attr, '')
                if attr_value and self._check_text_match(attr_value, patterns):
                    return True
        
        return False
    
    def detect_button(self, html_content: str, url: str, button_type: str) -> Tuple[bool, str]:
        """
        Detect if a specific button type exists
        
        Args:
            html_content: HTML content to search
            url: URL being scanned (for domain-specific rules)
            button_type: 'add_to_cart' or 'buy_now'
        
        Returns:
            Tuple of (found: bool, method: str)
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            domain = self._get_domain(url)
            
            # Get rules for button type
            button_rules = self.rules.get(button_type, {})
            
            # 1. Check domain-specific rules first
            domain_rules = button_rules.get("domains", {})
            for domain_pattern, rules in domain_rules.items():
                if domain_pattern in domain:
                    # Check domain-specific selectors
                    if "selectors" in rules:
                        if self._check_selector(soup, rules["selectors"]):
                            return True, f"domain_selector_{domain_pattern}"
                    
                    # Check domain-specific text
                    if "text" in rules:
                        if self._check_text_patterns(soup, rules["text"]):
                            return True, f"domain_text_{domain_pattern}"
            
            # 2. Check generic CSS selectors
            css_selectors = button_rules.get("css_selectors", [])
            if self._check_selector(soup, css_selectors):
                return True, "css_selector"
            
            # 3. Check generic text patterns
            text_patterns = button_rules.get("text_patterns", [])
            if self._check_text_patterns(soup, text_patterns):
                return True, "text_pattern"
            
            # Not found
            return False, "not_found"
        
        except Exception as e:
            return False, f"error: {str(e)}"
    
    def detect_all_buttons(self, html_content: str, url: str) -> Dict:
        """
        Detect both add_to_cart and buy_now buttons
        
        Returns:
            Dict with detection results
        """
        add_to_cart_found, add_to_cart_method = self.detect_button(
            html_content, url, "add_to_cart"
        )
        
        buy_now_found, buy_now_method = self.detect_button(
            html_content, url, "buy_now"
        )
        
        # Determine overall status
        if add_to_cart_found or buy_now_found:
            status = "available"
        else:
            status = "unavailable"
        
        return {
            "add_to_cart": add_to_cart_found,
            "add_to_cart_method": add_to_cart_method,
            "buy_now": buy_now_found,
            "buy_now_method": buy_now_method,
            "status": status
        }


# Create singleton instance
detector = ButtonDetector()
