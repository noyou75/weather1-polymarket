"""
Station seed data — Phase 4.
US cities relevant to Polymarket weather markets, based on Phase 0 analysis
and observed market types (city-specific temperature markets like 9985's strategy).

Only seeded once. NWS grid info is populated on first NWS fetch.
"""

STATIONS: list[dict] = [
    {
        "station_id": "NYC_LGA",
        "name": "New York City / LaGuardia",
        "city": "New York City",
        "state": "NY",
        "latitude": 40.7772,
        "longitude": -73.8726,
        "timezone": "America/New_York",
        "notes": "Key Polymarket market: 'Highest temp in NYC on date X?' — 9985 won $74K here",
    },
    {
        "station_id": "CHI_ORD",
        "name": "Chicago / O'Hare",
        "city": "Chicago",
        "state": "IL",
        "latitude": 41.9742,
        "longitude": -87.9073,
        "timezone": "America/Chicago",
        "notes": "Major city temperature market candidate",
    },
    {
        "station_id": "MIA_MIA",
        "name": "Miami / Miami International",
        "city": "Miami",
        "state": "FL",
        "latitude": 25.7959,
        "longitude": -80.2870,
        "timezone": "America/New_York",
        "notes": "Heat extremes; hurricane season relevance",
    },
    {
        "station_id": "PHX_SKY",
        "name": "Phoenix / Sky Harbor",
        "city": "Phoenix",
        "state": "AZ",
        "latitude": 33.4373,
        "longitude": -112.0078,
        "timezone": "America/Phoenix",
        "notes": "Extreme heat records; frequent Polymarket temperature markets",
    },
    {
        "station_id": "DAL_DAL",
        "name": "Dallas / Love Field",
        "city": "Dallas",
        "state": "TX",
        "latitude": 32.8481,
        "longitude": -96.8512,
        "timezone": "America/Chicago",
        "notes": "Temperature extreme market candidate",
    },
    {
        "station_id": "LAX_LAX",
        "name": "Los Angeles / LAX",
        "city": "Los Angeles",
        "state": "CA",
        "latitude": 33.9425,
        "longitude": -118.4081,
        "timezone": "America/Los_Angeles",
        "notes": "Temperature and heat wave markets",
    },
]
