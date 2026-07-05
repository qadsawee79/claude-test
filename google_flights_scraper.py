#!/usr/bin/env python3
"""
Google Flights Scraper
Scrapes Google Flights for flight data when API is unavailable
Use as fallback only - slower and less reliable than official APIs
"""
import json
from pathlib import Path
from typing import Optional, Dict, List
import datetime
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not installed. Install with: pip install selenium")


class GoogleFlightsScraper:
    """Scrape Google Flights for flight data (fallback)"""

    def __init__(self, preferences_file: str = "flight_preferences.json"):
        self.preferences_file = preferences_file
        self.preferences = self.load_preferences()
        self.price_history_file = "flight_price_history.json"
        self.price_history = self.load_price_history()
        self.driver = None

    def load_preferences(self) -> Dict:
        """Load saved user preferences"""
        try:
            if Path(self.preferences_file).exists():
                with open(self.preferences_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass

        return {
            "home_airport": "KWI",
            "default_currency": "KWD"
        }

    def load_price_history(self) -> List[Dict]:
        """Load price history"""
        try:
            if Path(self.price_history_file).exists():
                with open(self.price_history_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def save_price_history(self):
        """Save price history"""
        try:
            with open(self.price_history_file, 'w') as f:
                json.dump(self.price_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save price history: {e}")

    def record_price(self, route: str, depart_date: str, price: float, airline: str = ""):
        """Record price in history"""
        record = {
            "route": route,
            "depart_date": depart_date,
            "price": price,
            "airline": airline,
            "timestamp": datetime.datetime.now().isoformat(),
            "currency": self.preferences.get("default_currency", "KWD"),
            "source": "google_flights"
        }
        self.price_history.append(record)
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
        self.save_price_history()

    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            return None

        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            # Try to find Chrome
            self.driver = webdriver.Chrome(options=chrome_options)
            return self.driver
        except Exception as e:
            print(f"⚠️  Could not initialize Chrome: {e}")
            print("   Download ChromeDriver: https://chromedriver.chromium.org/")
            return None

    def _close_driver(self):
        """Close Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> Dict:
        """
        Search Google Flights using Selenium

        Args:
            origin: Origin airport code
            destination: Destination airport code
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date (optional)
            adults: Number of adults

        Returns:
            Dictionary with flight results
        """
        print("\n" + "=" * 70)
        print("✈️  GOOGLE FLIGHTS SCRAPER (Fallback)")
        print("=" * 70)
        print(f"\n🔍 Searching: {origin} → {destination}")
        print(f"   Departure: {depart_date}")
        if return_date:
            print(f"   Return: {return_date}")

        if not SELENIUM_AVAILABLE:
            return {
                "error": "Selenium not available",
                "message": "Install with: pip install selenium",
                "suggestion": "Also download ChromeDriver from https://chromedriver.chromium.org/"
            }

        driver = self._init_driver()
        if not driver:
            return {
                "error": "Chrome driver not found",
                "message": "Could not initialize Selenium WebDriver",
                "suggestion": "Download ChromeDriver: https://chromedriver.chromium.org/"
            }

        try:
            print("\n   Opening Google Flights...", end=" ", flush=True)

            # Build URL
            trip_type = "r" if return_date else "o"
            url = (f"https://www.google.com/flights?"
                   f"hl=en&curr={self.preferences.get('default_currency', 'KWD')}"
                   f"&flt={origin}.{destination}.{depart_date.replace('-', '')}")

            if return_date:
                url += f".{return_date.replace('-', '')}"

            url += f".{trip_type}_{adults}_{0}_{0}"

            driver.get(url)
            print("✅")

            # Wait for page to load
            print("   Waiting for results...", end=" ", flush=True)
            time.sleep(3)

            # Extract prices - this varies based on Google's HTML structure
            # Using multiple selectors as backup
            selectors = [
                "span[data-airfare]",
                ".nKJZLe",  # Price element
                "div.qqt6t span",
            ]

            prices = []
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        prices = [e.text for e in elements if e.text and any(c.isdigit() for c in e.text)]
                        if prices:
                            break
                except:
                    continue

            print("✅\n")

            # Process results
            results = {
                "route": f"{origin} → {destination}",
                "trip_type": "Round Trip" if return_date else "One Way",
                "depart_date": depart_date,
                "return_date": return_date,
                "passengers": {"adults": adults},
                "currency": self.preferences.get("default_currency", "KWD"),
                "flights": [],
                "note": "From Google Flights (fallback source)"
            }

            if prices:
                for i, price_str in enumerate(prices[:10], 1):
                    try:
                        # Extract numeric price
                        price = float(''.join(c for c in price_str if c.isdigit() or c == '.'))

                        flight_info = {
                            "rank": i,
                            "price": price,
                            "airline": "See Google Flights for details",
                            "note": "Full details available on Google Flights"
                        }
                        results["flights"].append(flight_info)

                        # Record price
                        self.record_price(
                            f"{origin} → {destination}",
                            depart_date,
                            price
                        )
                    except:
                        continue
            else:
                results["flights"] = [
                    {
                        "note": "Could not extract prices. Visit google.com/flights manually",
                        "url": url
                    }
                ]

            return results

        except Exception as e:
            print(f"❌")
            return {
                "error": type(e).__name__,
                "message": str(e),
                "suggestion": "Try again or use official API"
            }
        finally:
            self._close_driver()

    def format_results(self, results: Dict) -> str:
        """Format search results for display"""
        if "error" in results:
            return f"❌ Error: {results.get('error')}\n   {results.get('message', '')}\n   Suggestion: {results.get('suggestion', '')}"

        output = []
        output.append("\n" + "=" * 70)
        output.append("📊 GOOGLE FLIGHTS RESULTS (Fallback)")
        output.append("=" * 70)

        output.append(f"\n✈️  {results['route']}")
        output.append(f"   Type: {results['trip_type']}")
        output.append(f"   Depart: {results['depart_date']}")
        if results['return_date']:
            output.append(f"   Return: {results['return_date']}")
        output.append(f"   Currency: {results['currency']}")

        if results.get('note'):
            output.append(f"\n   📌 {results['note']}")

        flights = results.get('flights', [])
        if not flights:
            output.append("\n   ⚠️  No flights found")
        else:
            output.append(f"\n   Found {len(flights)} prices:\n")
            for flight in flights[:5]:
                if flight.get('price'):
                    price = flight.get('price', 'N/A')
                    output.append(f"   {flight['rank']}. {price:>8.0f} {results['currency']}")
                else:
                    output.append(f"\n   {flight.get('note', '')}")

        output.append("\n   💡 For detailed information, visit: google.com/flights")
        output.append("=" * 70 + "\n")
        return "\n".join(output)


def main():
    """Example usage"""
    print("\n" + "=" * 70)
    print("GOOGLE FLIGHTS SCRAPER - SETUP DEMO")
    print("=" * 70)

    scraper = GoogleFlightsScraper()

    if not SELENIUM_AVAILABLE:
        print("\n⚠️  SETUP REQUIRED")
        print("\nSelenium is not installed.")
        print("\nTo use this scraper, install the package:")
        print("\n   pip install selenium")
        print("\nThen download ChromeDriver:")
        print("   https://chromedriver.chromium.org/")
        print("\nAdd to PATH or specify path in code:")
        print("   webdriver.Chrome('/path/to/chromedriver')")
        print("\n" + "=" * 70 + "\n")
        return

    # Example search
    print("\n[1] SEARCHING GOOGLE FLIGHTS")
    print("-" * 70)
    results = scraper.search_flights(
        origin="KWI",
        destination="LHR",
        depart_date="2025-12-22"
    )
    print(scraper.format_results(results))

    print("\n" + "=" * 70)
    print("✅ Google Flights Scraper Ready (Use as Fallback)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
