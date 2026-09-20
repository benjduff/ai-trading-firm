from dataclasses import dataclass
from datetime import date, datetime, timezone

import httpx

from app.config import settings

BASE_URL = "https://api.polygon.io"


class MarketDataError(Exception):
    pass


@dataclass
class DailyBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


def fetch_daily_bars(ticker: str, start: date, end: date) -> list:
    if not settings.polygon_api_key:
        raise MarketDataError("POLYGON_API_KEY is not set; add it to apps/api/.env")

    url = (
        f"{BASE_URL}/v2/aggs/ticker/{ticker.upper()}/range/1/day/"
        f"{start.isoformat()}/{end.isoformat()}"
    )
    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {settings.polygon_api_key}"},
            params={"adjusted": "true", "sort": "asc", "limit": 50000},
        )
    response.raise_for_status()
    payload = response.json()

    status = payload.get("status")
    if status not in ("OK", "DELAYED"):
        raise MarketDataError(
            f"Polygon request failed for {ticker}: {payload.get('error') or status}"
        )

    results = payload.get("results") or []
    if not results:
        raise MarketDataError(
            f"no price data returned for {ticker} in range {start}..{end}"
        )

    return [
        DailyBar(
            date=datetime.fromtimestamp(r["t"] / 1000, tz=timezone.utc).date(),
            open=r["o"],
            high=r["h"],
            low=r["l"],
            close=r["c"],
            volume=r["v"],
        )
        for r in results
    ]
