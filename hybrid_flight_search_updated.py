#!/usr/bin/env python3
"""
Hybrid Flight Search System - Updated
Primary: Kiwi.com API (Free, reliable)
Fallback: Google Flights Scraper (When needed)
"""
import json
from pathlib import Path
from typing import Optional, Dict

from kiwi_skill import KiwiFlightSkill
from google_flights_scraper import GoogleFlightsScraper


class HybridFlightSearch:
    """
    Hybrid flight search combining multiple FREE sources
    Tries Kiwi.com first, falls back to Google Flights if needed
    """

    def __init__(self):
        """Initialize with both primary and fallback sources"""
        print("\n" + "=" * 70)
        print("🚀 HYBRID FLIGHT SEARCH SYSTEM (FREE)")
        print("=" * 70)

        # Primary: Kiwi.com API (Free!)
        print("\n[1] Initializing Kiwi.com API (Primary)...", end=" ")
        self.kiwi = KiwiFlightSkill()

        if self.kiwi.available:
            print("✅")
        else:
            print("⚠️ Not available")

        # Fallback: Google Flights Scraper
        print("[2] Initializing Google Flights (Fallback)...", end=" ")
        try:
            self.google_flights = GoogleFlightsScraper()
            print("✅")
        except Exception as e:
            print(f"⚠️ {e}")
            self.google_flights = None

        self.last_search_source = None

    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        cabin_class: str = "M",
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
            cabin_class: "M"=economy, "C"=business, "F"=first
            force_fallback: Force use of fallback source

        Returns:
            Flight results with source info
        """
        print("\n" + "=" * 70)
        print("🛫 HYBRID FLIGHT SEARCH")
        print("=" * 70)

        results = None

        # Try primary source first
        if not force_fallback and self.kiwi.available:
            print("\n📍 Trying Primary Source: Kiwi.com")
            print("-" * 70)

            results = self.kiwi.search_flights(
                origin=origin,
                destination=destination,
                depart_date=depart_date,
                return_date=return_date,
                adults=adults,
                children=children,
                cabin_class=cabin_class
            )

            if "error" not in results or len(results.get("flights", [])) > 0:
                self.last_search_source = "kiwi"
                results["source"] = "Kiwi.com (Free API)"
                return results

            # Primary failed, try fallback
            print("\n⚠️  Kiwi.com failed, trying fallback...")

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
                "message": "Neither Kiwi.com nor Google Flights working",
                "suggestion": "Check internet connection and try again"
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

        # Get Kiwi.com results
        print("\n[1] Kiwi.com API...", end=" ")
        kiwi_results = self.kiwi.search_flights(
            origin=origin,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults
        )
        kiwi_status = "✅" if "error" not in kiwi_results else "❌"
        print(kiwi_status)

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
            "kiwi": {
                "status": "✅ Available" if not kiwi_results.get("error") else "❌ Failed",
                "flights_found": len(kiwi_results.get("flights", [])),
                "cheapest_price": None
            },
            "google_flights": {
                "status": "✅ Available" if google_results and not google_results.get("error") else "❌ Failed",
                "flights_found": len(google_results.get("flights", [])) if google_results else 0,
                "cheapest_price": None
            }
        }

        # Extract cheapest prices
        if kiwi_results.get("flights"):
            prices = [f.get("price") for f in kiwi_results["flights"] if isinstance(f.get("price"), (int, float))]
            if prices:
                comparison["kiwi"]["cheapest_price"] = min(prices)
                print(f"\nKiwi.com: {len(prices)} prices found, cheapest {min(prices)} KWD")

        if google_results and google_results.get("flights"):
            prices = [f.get("price") for f in google_results["flights"] if isinstance(f.get("price"), (int, float))]
            if prices:
                comparison["google_flights"]["cheapest_price"] = min(prices)
                print(f"Google Flights: {len(prices)} prices found, cheapest {min(prices)} KWD")

        print("\n" + "=" * 70 + "\n")

        return comparison

    def format_results(self, results: Dict) -> str:
        """Format results for display"""
        if results.get("source") == "Kiwi.com (Free API)":
            return self.kiwi.format_results(results)
        elif results.get("source") == "Google Flights (Scraper)":
            return self.google_flights.format_results(results)
        else:
            # Error formatting
            return f"❌ Error: {results.get('error')}\n   {results.get('message', '')}\n   {results.get('suggestion', '')}"


def main():
    """Example usage"""
    print("\n" + "=" * 70)
    print("HYBRID FLIGHT SEARCH - SETUP DEMO")
    print("=" * 70)

    # Initialize system
    hybrid = HybridFlightSearch()

    print("\n" + "=" * 70)
    print("✅ READY TO USE - NO CREDENTIALS NEEDED!")
    print("=" * 70)

    print("\n🎉 This system is 100% FREE:")
    print("   • Kiwi.com API - Free (no registration)")
    print("   • Google Flights - Free (no registration)")
    print("   • No payment needed, ever!")

    print("\n" + "=" * 70)
    print("EXAMPLE USAGE")
    print("=" * 70)

    print("\nBasic search:")
    print("   results = hybrid.search_flights('KWI', 'LHR', '2025-12-22')")
    print("   print(hybrid.format_results(results))")

    print("\nRound trip:")
    print("   results = hybrid.search_flights(")
    print("       'KWI', 'LHR', '2025-12-22', '2025-12-29'")
    print("   )")

    print("\nCompare sources:")
    print("   comparison = hybrid.compare_sources('KWI', 'LHR', '2025-12-22')")

    print("\n" + "=" * 70)
    print("✅ Ready to search flights!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
