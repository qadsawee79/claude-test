#!/usr/bin/env python3
"""
Kiwi.com Flight Search Skill
Free alternative to Amadeus - reliable flight data
"""
import json
from pathlib import Path
from typing import Optional, Dict, List
import datetime
import requests

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests not installed. Install with: pip install requests")


class KiwiFlightSkill:
    """Flight search using free Kiwi.com API"""

    # Kiwi.com API endpoint (free tier)
    KIWI_API_URL = "https://tequila-api.kiwi.com"

    def __init__(self, preferences_file: str = "flight_preferences.json"):
        self.preferences_file = preferences_file
        self.preferences = self.load_preferences()
        self.available = REQUESTS_AVAILABLE

        self.price_history_file = "flight_price_history.json"
        self.price_history = self.load_price_history()

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
            "preferred_cabin": "M",  # M=economy, C=business, F=first
            "default_currency": "KWD",
            "default_market": "KW"
        }

    def save_preferences(self):
        """Save user preferences"""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save preferences: {e}")

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
            "source": "kiwi"
        }
        self.price_history.append(record)
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-1000:]
        self.save_price_history()

    def search_flights(
        self,
        origin: str,
        destination: str,
        depart_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        cabin_class: str = "M",
        max_results: int = 10
    ) -> Dict:
        """
        Search for flights on Kiwi.com (Free API)

        Args:
            origin: Origin airport code (e.g., "KWI")
            destination: Destination airport code (e.g., "LHR")
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trips (optional)
            adults: Number of adults
            children: Number of children
            cabin_class: "M"=economy, "C"=business, "F"=first
            max_results: Maximum results to return

        Returns:
            Dictionary with flight results
        """
        print("\n" + "=" * 70)
        print("✈️  KIWI.COM FLIGHT SEARCH")
        print("=" * 70)
        print(f"\n🔍 Searching: {origin} → {destination}")
        print(f"   Departure: {depart_date}")
        if return_date:
            print(f"   Return: {return_date}")
        print(f"   Passengers: {adults} adult(s)", end="")
        if children:
            print(f", {children} child(ren)", end="")
        print()

        if not self.available:
            return {
                "error": "Requests library not available",
                "message": "Install with: pip install requests",
                "suggestion": "Run: python -m pip install requests"
            }

        try:
            print("\n   Querying Kiwi.com...", end=" ", flush=True)

            # Prepare search params for Kiwi API
            params = {
                "fly_from": origin.upper(),
                "fly_to": destination.upper(),
                "date_from": depart_date.replace("-", ""),
                "date_to": depart_date.replace("-", ""),
                "adults": adults,
                "children": children,
                "curr": self.preferences.get("default_currency", "KWD"),
                "limit": max_results,
                "sort": "price",
                "one_stop_limit": 1
            }

            if return_date:
                params["return_from"] = return_date.replace("-", "")
                params["return_to"] = return_date.replace("-", "")

            # Make request to Kiwi API
            response = requests.get(
                f"{self.KIWI_API_URL}/v2/search",
                params=params,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )

            if response.status_code != 200:
                print(f"❌")
                return {
                    "error": f"API Error {response.status_code}",
                    "message": response.text if response.text else "Unknown error",
                    "suggestion": "Check airport codes and try again"
                }

            data = response.json()
            print("✅\n")

            # Process results
            results = {
                "route": f"{origin} → {destination}",
                "trip_type": "Round Trip" if return_date else "One Way",
                "depart_date": depart_date,
                "return_date": return_date,
                "passengers": {
                    "adults": adults,
                    "children": children
                },
                "currency": self.preferences.get("default_currency", "KWD"),
                "flights": [],
                "debug": f"Found {len(data.get('data', []))} flights"
            }

            # Format flights
            for i, flight in enumerate(data.get('data', [])[:max_results], 1):
                try:
                    price = float(flight.get('price', 0))
                    airline = flight.get('airlines', ['Unknown'])[0] if flight.get('airlines') else 'Unknown'
                    stops = flight.get('stops', 0)
                    duration = flight.get('duration', {}).get('total', 0)

                    # Convert duration to readable format
                    hours = duration // 3600
                    minutes = (duration % 3600) // 60
                    duration_str = f"{hours}h{minutes}m"

                    flight_info = {
                        "rank": i,
                        "price": price,
                        "airline": airline,
                        "duration": duration_str,
                        "stops": stops,
                        "departure": flight.get('local_departure', ''),
                        "arrival": flight.get('local_arrival', ''),
                        "direct": stops == 0
                    }
                    results["flights"].append(flight_info)

                    # Record price
                    self.record_price(
                        f"{origin} → {destination}",
                        depart_date,
                        price,
                        airline
                    )
                except Exception as e:
                    print(f"Warning parsing flight: {e}")
                    continue

            return results

        except requests.Timeout:
            print(f"❌")
            return {
                "error": "Request Timeout",
                "message": "Kiwi.com API took too long to respond",
                "suggestion": "Try again later"
            }
        except Exception as e:
            print(f"❌")
            return {
                "error": type(e).__name__,
                "message": str(e),
                "suggestion": "Check internet connection and try again"
            }

    def format_results(self, results: Dict) -> str:
        """Format search results for display"""
        if "error" in results:
            return f"❌ Error: {results.get('error')}\n   {results.get('message', '')}\n   Suggestion: {results.get('suggestion', '')}"

        output = []
        output.append("\n" + "=" * 70)
        output.append("📊 SEARCH RESULTS (Kiwi.com)")
        output.append("=" * 70)

        output.append(f"\n✈️  {results['route']}")
        output.append(f"   Type: {results['trip_type']}")
        output.append(f"   Depart: {results['depart_date']}")
        if results['return_date']:
            output.append(f"   Return: {results['return_date']}")

        passengers = results['passengers']
        pax_str = f"{passengers['adults']} adult(s)"
        if passengers.get('children'):
            pax_str += f", {passengers['children']} child(ren)"
        output.append(f"   Passengers: {pax_str}")
        output.append(f"   Currency: {results['currency']}")

        flights = results.get('flights', [])
        if not flights:
            output.append("\n   ⚠️  No flights found")
        else:
            output.append(f"\n   Found {len(flights)} options:\n")
            for flight in flights[:5]:
                price = flight.get('price', 'N/A')
                stops = flight.get('stops', 0)
                direct = "✈️ Direct" if stops == 0 else f"↻ {stops} stop(s)"
                duration = flight.get('duration', '')
                airline = flight.get('airline', 'Unknown')

                output.append(f"   {flight['rank']}. {price:>8.0f} {results['currency']}  |  {airline}")
                output.append(f"      {direct} | {duration}")
                if flight.get('departure'):
                    output.append(f"      Depart: {flight.get('departure')} → Arrive: {flight.get('arrival')}")
                output.append("")

        output.append("=" * 70 + "\n")
        return "\n".join(output)


def main():
    """Example usage"""
    print("\n" + "=" * 70)
    print("KIWI.COM FLIGHT SKILL - DEMO")
    print("=" * 70)

    skill = KiwiFlightSkill()

    if not skill.available:
        print("\n⚠️  SETUP REQUIRED")
        print("\nRequests library is not installed.")
        print("\nTo use this skill, install the package:")
        print("\n   pip install requests")
        print("\n" + "=" * 70 + "\n")
        return

    # Example search
    print("\n[1] SEARCHING FOR FLIGHTS")
    print("-" * 70)
    results = skill.search_flights(
        origin="KWI",
        destination="LHR",
        depart_date="2025-12-22",
        adults=1
    )
    print(skill.format_results(results))

    print("\n" + "=" * 70)
    print("✅ Kiwi.com Skill Ready!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
