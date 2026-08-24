import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from strategies.base_strategy import BaseStrategy

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

class GenericSelectorStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            strategy_id="generic_selector",
            name="Generic Selector & Keyword Monitor",
            description="Universal website monitor using CSS selectors, text matching, or keyword presence"
        )

    def inspect(self, target: Dict[str, Any]) -> Dict[str, Any]:
        target_url = target.get("target_url", "")
        movie_title = target.get("movie_title", "Custom Target")
        selector = target.get("selector", "")
        keyword = target.get("keyword", "Book Now")
        condition = target.get("condition", "EXISTS").upper()  # EXISTS, NOT_EXISTS, KEYWORD_CONTAINS

        if not target_url:
            return self.format_result(
                status="ERROR",
                is_available=False,
                movie_title=movie_title,
                details="No target URL provided."
            )

        try:
            resp = requests.get(target_url, headers=HEADERS, timeout=12)
            if resp.status_code != 200:
                return self.format_result(
                    status="ERROR",
                    is_available=False,
                    movie_title=movie_title,
                    details=f"HTTP status error: {resp.status_code}"
                )

            soup = BeautifulSoup(resp.text, 'html.parser')
            is_available = False
            details = ""

            if selector:
                elements = soup.select(selector)
                if condition == "EXISTS" and len(elements) > 0:
                    is_available = True
                    details = f"Selector '{selector}' matched {len(elements)} element(s)."
                elif condition == "NOT_EXISTS" and len(elements) == 0:
                    is_available = True
                    details = f"Selector '{selector}' no longer present on page."
                elif condition == "KEYWORD_CONTAINS":
                    found = any(keyword.lower() in el.get_text().lower() for el in elements)
                    is_available = found
                    details = f"Selector '{selector}' matched and keyword '{keyword}' {'found' if found else 'not found'}."
            else:
                # Page level keyword match
                page_text = soup.get_text(separator=' ', strip=True).lower()
                is_available = keyword.lower() in page_text
                details = f"Keyword '{keyword}' {'found' if is_available else 'not found'} on target page."

            status = "AVAILABLE" if is_available else "UNAVAILABLE"
            return self.format_result(
                status=status,
                is_available=is_available,
                movie_title=movie_title,
                booking_url=target_url if is_available else None,
                details=details,
                raw_match={"selector": selector, "keyword": keyword}
            )

        except Exception as e:
            return self.format_result(
                status="ERROR",
                is_available=False,
                movie_title=movie_title,
                details=f"Generic check error: {str(e)}"
            )
