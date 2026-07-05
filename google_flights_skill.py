#!/usr/bin/env python3
"""
Google Flights Search Skill
Direct integration with Google Flights for reliable flight searching
"""
import datetime
from typing import Optional, Dict, List
import json
from pathlib import Path

# Try to import available Google Flights libraries
try:
    from google_flights_api import GoogleFlightsApi
    GOOGLE_FLIGHTS_AVAILABLE = True
except ImportError:
    GOOGLE_FLIGHTS_AVAILABLE = False
    print("⚠️  google-flights-api not installed. Install with: pip install google-flights-api")


class GoogleFlightsSkill:
    """Flight search skill using Google Flights"""

    def __init__(self, preferences_file: str = "flight_preferences.json"):
        self.preferences_file = preferences_file
        self.preferences = self.load_preferences()

        if GOOGLE_FLIGHTS_AVAILABLE:
            self.api = GoogleFlightsApi()
        else:
            self.api = None

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
            "preferred_cabin": "economy",
            "frequent_routes": [],
            "default_adults": 1,
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
        except Exception as e:
            print(f"Warning: Could not load price history: {e}")
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
            "currency": self.preferences.get("default_currency", "KWD")
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
        infants: int = 0,
        cabin_class: str = "economy"
    ) -> Dict:
        """
        Search for flights on Google Flights

        Args:
            origin: Origin airport code (e.g., "KWI")
            destination: Destination airport code (e.g., "LHR")
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trips (optional)
            adults: Number of adults
            children: Number of children
            infants: Number of infants
            cabin_class: "economy", "premium_economy", "business", "first"

        Returns:
            Dictionary with flight results
        """
        print("\n" + "=" * 70)
        print("✈️  GOOGLE FLIGHTS SEARCH")
        print("=" * 70)
        print(f"\n🔍 Searching: {origin} → {destination}")
        print(f"   Departure: {depart_date}")
        if return_date:
            print(f"   Return: {return_date}")
        print(f"   Passengers: {adults} adult(s)", end="")
        if children:
            print(f", {children} child(ren)", end="")
        if infants:
            print(f", {infants} infant(s)", end="")
        print()

        if not GOOGLE_FLIGHTS_AVAILABLE:
            return {
                "error": "Google Flights API not available",
                "message": "Install with: pip install google-flights-api",
                "suggestion": "Run: python -m pip install google-flights-api"
            }

        try:
            # Prepare search parameters
            search_params = {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": depart_date,
                "adults": adults,
                "children": children,
                "infants": infants,
                "currency": self.preferences.get("default_currency", "KWD")
            }

            # Add optional parameters
            if return_date:
                search_params["return_date"] = return_date

            # Map cabin class
            cabin_map = {
                "economy": "ECONOMY",
                "premium_economy": "PREMIUM_ECONOMY",
                "business": "BUSINESS",
                "first": "FIRST"
            }
            if cabin_class.lower() in cabin_map:
                search_params["cabin_class"] = cabin_map[cabin_class.lower()]

            # Perform search
            print("\n   Querying Google Flights...", end=" ", flush=True)
            flights = self.api.get_flights(**search_params)
            print("✅\n")

            # Process results
            results = {
                "route": f"{origin} → {destination}",
                "trip_type": "Round Trip" if return_date else "One Way",
                "depart_date": depart_date,
                "return_date": return_date,
                "passengers": {
                    "adults": adults,
                    "children": children,
                    "infants": infants
                },
                "currency": self.preferences.get("default_currency", "KWD"),
                "flights": []
            }

            # Format flights
            if isinstance(flights, list) and flights:
                for i, flight in enumerate(flights[:10], 1):
                    flight_info = {
                        "rank": i,
                        "price": flight.get("price"),
                        "airline": flight.get("airline", "Unknown"),
                        "duration": flight.get("duration"),
                        "departure": flight.get("departure_time"),
                        "arrival": flight.get("arrival_time"),
                        "stops": flight.get("stops", 0),
                        "direct": flight.get("stops", 0) == 0
                    }
                    results["flights"].append(flight_info)

                    # Record price in history
                    if flight.get("price"):
                        self.record_price(
                            f"{origin} → {destination}",
                            depart_date,
                            float(str(flight.get("price", 0)).replace(",", "")),
                            flight.get("airline", "Unknown")
                        )

            return results

        except Exception as e:
            print(f"❌")
            return {
                "error": type(e).__name__,
                "message": str(e),
                "suggestion": "Check internet connection or try different search parameters"
            }

    def format_results(self, results: Dict) -> str:
        """Format search results for display"""
        if "error" in results:
            return f"❌ Error: {results.get('error')}\n   {results.get('message', '')}"

        output = []
        output.append("\n" + "=" * 70)
        output.append("📊 SEARCH RESULTS")
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
        if passengers.get('infants'):
            pax_str += f", {passengers['infants']} infant(s)"
        output.append(f"   Passengers: {pax_str}")
        output.append(f"   Currency: {results['currency']}")

        flights = results.get('flights', [])
        if not flights:
            output.append("\n   ⚠️  No flights found")
        else:
            output.append(f"\n   Found {len(flights)} options:\n")
            for flight in flights[:5]:
                price = flight.get('price', 'N/A')
                airline = flight.get('airline', 'Unknown')
                stops = flight.get('stops', 0)
                direct = "✈️ Direct" if stops == 0 else f"↻ {stops} stop(s)"
                duration = flight.get('duration', '')

                output.append(f"   {flight['rank']}. {price:>8} {results['currency']}  |  {airline}")
                output.append(f"      {direct} | {duration}")
                if flight.get('departure'):
                    output.append(f"      Depart: {flight.get('departure')} → Arrive: {flight.get('arrival')}")
                output.append("")

        output.append("=" * 70 + "\n")
        return "\n".join(output)

    def set_price_alert(self, origin: str, destination: str, max_price: float,
                       depart_date: str, return_date: Optional[str] = None) -> Dict:
        """Set a price alert (saves to preferences)"""
        if "alerts" not in self.preferences:
            self.preferences["alerts"] = []

        alert = {
            "id": f"{origin}-{destination}-{depart_date}",
            "origin": origin,
            "destination": destination,
            "max_price": max_price,
            "depart_date": depart_date,
            "return_date": return_date,
            "created_date": datetime.datetime.now().isoformat(),
            "status": "active"
        }

        self.preferences["alerts"].append(alert)
        self.save_preferences()

        return {
            "status": "alert_set",
            "message": f"✅ Alert set: {origin} → {destination} below {max_price} {self.preferences.get('default_currency', 'KWD')}"
        }

    def list_alerts(self) -> Dict:
        """List all saved alerts"""
        alerts = self.preferences.get("alerts", [])
        return {
            "total_alerts": len(alerts),
            "alerts": alerts
        }


def main():
    """Example usage"""
    print("\n" + "=" * 70)
    print("GOOGLE FLIGHTS SKILL - DEMO")
    print("=" * 70)

    skill = GoogleFlightsSkill()

    if not GOOGLE_FLIGHTS_AVAILABLE:
        print("\n⚠️  SETUP REQUIRED")
        print("\nGoogle Flights API is not installed.")
        print("\nTo use this skill, install the required package:")
        print("\n   pip install google-flights-api")
        print("\nThen try again.")
        print("\n" + "=" * 70 + "\n")
        return

    # Example 1: Simple one-way search
    print("\n[1] ONE-WAY FLIGHT SEARCH")
    print("-" * 70)
    results = skill.search_flights(
        origin="KWI",
        destination="LHR",
        depart_date="2025-12-22"
    )
    print(skill.format_results(results))

    # Example 2: Round-trip search
    print("\n[2] ROUND-TRIP FLIGHT SEARCH")
    print("-" * 70)
    results = skill.search_flights(
        origin="KWI",
        destination="DXB",
        depart_date="2025-12-20",
        return_date="2025-12-27",
        adults=2
    )
    print(skill.format_results(results))

    # Example 3: Set price alert
    print("\n[3] SETTING PRICE ALERT")
    print("-" * 70)
    alert = skill.set_price_alert(
        origin="KWI",
        destination="LHR",
        max_price=400,
        depart_date="2025-12-22"
    )
    print(f"{alert['message']}")

    # Example 4: List alerts
    print("\n[4] LISTING ALERTS")
    print("-" * 70)
    alerts = skill.list_alerts()
    print(f"Total alerts: {alerts['total_alerts']}")
    for alert in alerts['alerts']:
        print(f"  • {alert['origin']} → {alert['destination']}: max {alert['max_price']} KWD")

    print("\n" + "=" * 70)
    print("✅ Google Flights Skill Demo Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
