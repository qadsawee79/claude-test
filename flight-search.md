# Flight Search Skill

**Purpose:** Streamlined flight searching using the Skyscanner MCP server

**Usage:** `/flight-search <query>`

## Examples

```
/flight-search search Kuwait to London December 22-29
```

```
/flight-search find flights KWI to DXB next week, business class
```

```
/flight-search round trip from Kuwait to Dubai departing December 20
```

## Features

- 🎯 **Natural Language:** Parse dates like "next week", "December 22", "next month"
- 💾 **Preferences:** Remember your home airport and favorite routes
- 💷 **KWD Currency:** All prices in Kuwaiti Dinars
- ✈️ **Trip Types:** One-way, round-trip, and multi-city searches
- 🎫 **Cabin Classes:** Economy, Premium Economy, Business, First Class
- 📊 **Formatted Results:** Clean, easy-to-read flight listings

## Supported Queries

### Simple Searches
- "Find flights from Kuwait to London"
- "Search KWI to LHR December 22"
- "Flights from Dubai to Paris next week"

### Natural Dates
- "next week" → 7 days from today
- "next month" → 30 days from today
- "in 5 days" → specific number of days
- "2025-12-22" → ISO format

### Trip Types
- Round trip: "From Kuwait to London December 22-29"
- One-way: "Kuwait to London December 22"
- Return: Specify both depart_date and return_date

### Cabin Classes
- "economy" (default)
- "premium_economy"
- "business"
- "first"

### Passengers
- "1 adult" (default)
- "2 adults, 1 child"
- "4 passengers"

## Example Queries

```
Search for round-trip flights from Kuwait to London
Departure: December 22, 2025
Return: December 29, 2025
Cabin: Economy
Passengers: 1 adult
```

**Output:**
```
✈️  KWI → LHR
   Type: Round Trip
   Depart: 2025-12-22
   Return: 2025-12-29
   Cabin: Economy
   Passengers: 1

   Found 8 options:

   1.    450 KWD  |  ✈️ Direct
      Depart: 08:30
      Arrive: 16:45

   2.    520 KWD  |  ↻ Connecting
      Depart: 10:15
      Arrive: 20:30

   3.    380 KWD  |  ↻ Connecting
      Depart: 14:00
      Arrive: 23:15
```

## Saved Preferences

The skill remembers your preferences:
- Home airport (default: KWI)
- Preferred cabin class (default: economy)
- Number of adults (default: 1)
- Frequent routes

**To reset preferences:**
Delete `flight_preferences.json` in the mcp-skyscanner folder.

## Error Handling

If Skyscanner API is rate limited:
- ⏳ Wait 5-10 minutes and try again
- 🔄 Try with specific airport codes (KWI, LHR, DXB) instead of city names
- 📍 Simpler searches often succeed when complex ones fail

## Tips & Tricks

- **Use airport codes** for faster, more reliable searches: "KWI", "LHR", "DXB"
- **Off-peak times** (10 PM - 6 AM) may have better API availability
- **Specify exact dates** rather than natural language for best results
- **Try again later** if you get rate limit errors

## Integration with Claude Desktop

This skill works alongside the Skyscanner MCP server in Claude Desktop:
- When you ask Claude about flights, it can use the MCP tools directly
- This skill provides a streamlined interface in Claude Code
- Combine both for maximum flexibility

## Troubleshooting

**"Could not find airport"**
- Try using IATA code (KWI, LHR, DXB) instead of city name
- City names might be ambiguous; codes are unambiguous

**"API Rate Limited"**
- Skyscanner is blocking automated requests
- Wait 10+ minutes before retrying
- Try fewer/simpler searches

**"Invalid date format"**
- Dates must be in the future
- Use YYYY-MM-DD format or natural language (next week, December 22)

**No results found**
- The route might not be available
- Try different dates or airports
- Check if the dates are far enough in advance
