"""Minimal, standalone price lookup for the mock broker. Deliberately not shared
with apps/api's app.quant.market_data - this service imports nothing from the
research app, by design."""

from datetime import date, timedelta

import httpx

from app.config import settings


class MarketDataError(Exception):
    pass


def fetch_last_close(ticker: str) -> float:
    if not settings.polygon_api_key:
        raise MarketDataError("POLYGON_API_KEY is not set; add it to apps/execution/.env")

    end = date.today()
    start = end - timedelta(days=10)
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker.upper()}/range/1/day/"
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

    results = payload.get("results") or []
    if not results:
        raise MarketDataError(f"no price data returned for {ticker}")

    return results[-1]["c"]
