import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from strategies.base_strategy import BaseStrategy

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}

class VictoryCinemaStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            strategy_id="victory_cinema",
            name="Victory Cinema Release Tracker",
            description="Dedicated detector for Victory Cinema (victorycinema.in) checking upcoming & showtime pages"
        )

    def inspect(self, target: Dict[str, Any]) -> Dict[str, Any]:
        target_url = target.get("target_url", "https://victorycinema.in/upcoming-movie/toxic-kannada-with-english-subtitles/")
        movie_title = target.get("movie_title", "Toxic (Kannada)")
        showing_url = "https://victorycinema.in/showing/"

        detected_booking_url = None
        is_available = False
        status = "COMING_SOON"
        details_list = []

        try:
            # Step 1: Check main movie upcoming page
            resp = requests.get(target_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                page_text = soup.get_text(separator=' ', strip=True).lower()

                # Look for booking links on the page (excluding standard generic navigation)
                booking_links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    link_text = a.get_text(strip=True).lower()
                    if ('booking/' in href or 'book now' in link_text or 'select seat' in link_text) and not href.endswith('/showing/'):
                        booking_links.append(href)

                has_coming_soon = "coming soon" in page_text

                if booking_links:
                    is_available = True
                    status = "AVAILABLE"
                    detected_booking_url = booking_links[0]
                    if not detected_booking_url.startswith('http'):
                        detected_booking_url = 'https://victorycinema.in' + detected_booking_url
                    details_list.append(f"Active booking link detected: {detected_booking_url}")
                elif not has_coming_soon and ("book" in page_text or "showtime" in page_text):
                    is_available = True
                    status = "AVAILABLE"
                    detected_booking_url = target_url
                    details_list.append("'Coming Soon' badge removed & booking keywords detected.")
                else:
                    details_list.append("Upcoming page checked: Status is 'Coming Soon'.")
            else:
                details_list.append(f"Upcoming page returned HTTP status {resp.status_code}.")

            # Step 2: Fallback check on Now Showing page to see if Toxic is listed under current movies
            if not is_available:
                showing_resp = requests.get(showing_url, headers=HEADERS, timeout=12)
                if showing_resp.status_code == 200:
                    showing_soup = BeautifulSoup(showing_resp.text, 'html.parser')
                    showing_text = showing_soup.get_text(separator=' ', strip=True).lower()

                    if "toxic" in showing_text:
                        # Find toxic card or link
                        for a in showing_soup.find_all('a', href=True):
                            href = a['href']
                            if 'toxic' in href or ('toxic' in a.get_text(strip=True).lower() and 'booking' in href):
                                is_available = True
                                status = "AVAILABLE"
                                detected_booking_url = href if href.startswith('http') else 'https://victorycinema.in' + href
                                details_list.append(f"'Toxic' detected on Now Showing page! Booking link: {detected_booking_url}")
                                break

            details = " | ".join(details_list)
            return self.format_result(
                status=status,
                is_available=is_available,
                movie_title=movie_title,
                booking_url=detected_booking_url,
                details=details,
                raw_match={"url": target_url, "booking_url": detected_booking_url}
            )

        except Exception as e:
            return self.format_result(
                status="ERROR",
                is_available=False,
                movie_title=movie_title,
                details=f"Network/parsing error while checking Victory Cinema: {str(e)}"
            )
