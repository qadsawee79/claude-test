#!/usr/bin/env python3
"""
Hybrid Flight Search Skill
Primary: Amadeus API (reliable, official)
Fallback: Google Flights Scraper (when primary fails)
"""
import json
from pathlib import Path
from typing import Optional, Dict
import datetime

from amadeus_skill import AmadeusFlightSkill
from google_flights_scraper import GoogleFlightsScraper


class HybridFlightSearch:
    """
    Hybrid flight search combining multiple sources
    Tries Amadeus first, falls back to Google Flights if needed
    """

    def __init__(self, amadeus_client_id: Optional[str] = None,
                 amadeus_client_secret: Optional[str] = None):
        """Initialize with both primary and fallback sources"""
        print("\n" + "=" * 70)
        print("🚀 HYBRID FLIGHT SEARCH SYSTEM")
        print("=" * 70)

        # Primary: Amadeus API
        print("\n[1] Initializing Amadeus API (Primary)...", end=" ")
        self.amadeus = AmadeusFlightSkill(
            client_id=amadeus_client_id,
            client_secret=amadeus_client_secret
        )

        if self.amadeus.available:
            print("✅")
        else:
            print("⚠️ Not configured")

        # Fallback: Google Flights Scraper
        print("[2] Initializing Google Flights (Fallback)...", end=" ")
        try:
            self.google_flights = GoogleFlightsScraper()
            print("✅")
        except Exception as e:
            print(f"⚠️ {e}")
            self.google_flights = None

        self.last_search_source = None
        self.preferences_file = "flight_preferences.json"

    def configure_amadeus(self, client_id: str, client_secret: str) -> Dict:
        """Configure Amadeus API credentials"""
        print("\n🔧 Configuring Amadeus API...")
        result = self.amadeus.set_credentials(client_id, client_secret)
        print(f"   {result['message']}")
        return result

    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        cabin_class: str = "ECONOMY",
        force_fallback: bool = False
    ) -> Dict:
        """
        Search for flights with smart fallback

        Args:
            origin: Origin airport code
            destination: Destination airport code
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date (optional)
            adults: Number of adults
            children: Number of children
            cabin_class: Cabin class
            force_fallback: Force use of fallback source

        Returns:
            Flight results with source info
        """
        print("\n" + "=" * 70)
        print("🛫 HYBRID FLIGHT SEARCH")
        print("=" * 70)

        results = None

        # Try primary source first
        if not force_fallback and self.amadeus.available:
            print("\n📍 Trying Primary Source: Amadeus API")
            print("-" * 70)

            results = self.amadeus.search_flights(
                origin=origin,
                destination=destination,
                depart_date=depart_date,
                return_date=return_date,
                adults=adults,
                children=children,
                cabin_class=cabin_class
            )

            if "error" not in results or len(results.get("flights", [])) > 0:
                self.last_search_source = "amadeus"
                results["source"] = "Amadeus (Official API)"
                return results

            # Primary failed, try fallback
            print("\n⚠️  Amadeus failed, trying fallback...")

        # Use fallback source
        if self.google_flights:
            print("\n📍 Trying Fallback Source: Google Flights")
            print("-" * 70)

            results = self.google_flights.search_flights(
                origin=origin,
                destination=destination,
                depart_date=depart_date,
                return_date=return_date,
                adults=adults
            )

            if "error" not in results or len(results.get("flights", [])) > 0:
                self.last_search_source = "google_flights"
                results["source"] = "Google Flights (Scraper)"
                return results

        # All sources failed
        if not results:
            results = {
                "error": "No search sources available",
                "message": "Configure Amadeus API or install Selenium",
                "suggestion": "See setup guide for instructions"
            }

        return results

    def compare_sources(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1
    ) -> Dict:
        """
        Compare results from both sources

        Returns:
            Comparison results showing both sources
        """
        print("\n" + "=" * 70)
        print("🔀 COMPARING FLIGHT SOURCES")
        print("=" * 70)

        # Get Amadeus results
        print("\n[1] Amadeus API...", end=" ")
        amadeus_results = self.amadeus.search_flights(
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults
        )
        amadeus_status = "✅" if "error" not in amadeus_results else "❌"
        print(amadeus_status)

        # Get Google Flights results
        print("[2] Google Flights...", end=" ")
        google_results = self.google_flights.search_flights(
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults
        ) if self.google_flights else None
        google_status = "✅" if google_results and "error" not in google_results else "❌"
        print(google_status)

        # Compare
        print("\n" + "-" * 70)
        print("COMPARISON RESULTS")
        print("-" * 70)

        comparison = {
            "amadeus": {
                "status": "✅ Available" if not amadeus_results.get("error") else "❌ Failed",
                "flights_found": len(amadeus_results.get("flights", [])),
                "cheapest_price": None
            },
            "google_flights": {
                "status": "✅ Available" if google_results and not google_results.get("error") else "❌ Failed",
                "flights_found": len(google_results.get("flights", [])) if google_results else 0,
                "cheapest_price": None
            }
        }

        # Extract cheapest prices
        if amadeus_results.get("flights"):
            prices = [f.get("price") for f in amadeus_results["flights"] if isinstance(f.get("price"), (int, float))]
            if prices:
                comparison["amadeus"]["cheapest_price"] = min(prices)
                print(f"\nAmadeus: {len(prices)} prices found, cheapest {min(prices)} KWD")

        if google_results and google_results.get("flights"):
            prices = [f.get("price") for f in google_results["flights"] if isinstance(f.get("price"), (int, float))]
            if prices:
                comparison["google_flights"]["cheapest_price"] = min(prices)
                print(f"Google Flights: {len(prices)} prices found, cheapest {min(prices)} KWD")

        print("\n" + "=" * 70 + "\n")

        return comparison

    def format_results(self, results: Dict) -> str:
        """Format results for display"""
        if results.get("source") == "Amadeus (Official API)":
            return self.amadeus.format_results(results)
        elif results.get("source") == "Google Flights (Scraper)":
            return self.google_flights.format_results(results)
        else:
            # Error formatting
            return f"❌ Error: {results.get('error')}\n   {results.get('message', '')}\n   {results.get('suggestion', '')}"


def main():
    """Example usage"""
    print("\n" + "=" * 70)
    print("HYBRID FLIGHT SEARCH - DEMO")
    print("=" * 70)

    # Initialize system
    hybrid = HybridFlightSearch()

    print("\n" + "=" * 70)
    print("SETUP INSTRUCTIONS")
    print("=" * 70)

    print("\n📍 To enable Amadeus (Primary):")
    print("   1. Register: https://developers.amadeus.com/register")
    print("   2. Create app to get Client ID and Secret")
    print("   3. Run: hybrid.configure_amadeus('YOUR_ID', 'YOUR_SECRET')")

    print("\n📍 To enable Google Flights (Fallback):")
    print("   1. Install Selenium: pip install selenium")
    print("   2. Download ChromeDriver: https://chromedriver.chromium.org/")
    print("   3. Already configured!")

    print("\n" + "=" * 70)
    print("READY TO SEARCH")
    print("=" * 70)

    print("\nExample usage:")
    print("   results = hybrid.search_flights('KWI', 'LHR', '2025-12-22')")
    print("   print(hybrid.format_results(results))")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
