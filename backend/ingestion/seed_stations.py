"""Seed the WeatherStation table from the static station list."""
import logging
from sqlmodel import Session, select
from database import engine
from models.weather import WeatherStation
from ingestion.stations import STATIONS

logger = logging.getLogger("weather1.ingestion.seed")


def seed_stations_if_empty() -> int:
    """Insert seeded stations if the table is empty. Returns count inserted."""
    with Session(engine, expire_on_commit=False) as s:
        existing = s.exec(select(WeatherStation)).all()
        if existing:
            return 0
        for st in STATIONS:
            s.add(WeatherStation(**st))
        s.commit()
    logger.info("Seeded %d weather stations", len(STATIONS))
    return len(STATIONS)
