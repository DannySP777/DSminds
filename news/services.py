"""
news/services.py

Fuente de noticias: Yahoo Finance vía la librería `yfinance` (gratuita,
sin API key). Se piden las noticias por cada ticker que también usa el
scanner (scanner/services.py) para que noticias y resultados del scan
queden correlacionados por símbolo.
"""
from datetime import datetime, timezone

import requests
import yfinance as yf

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
CALENDAR_IMPACT_MAP = {"Low": "low", "Medium": "medium", "High": "high"}
RELEVANT_IMPACTS = {"Medium", "High"}  # 2 y 3 estrellas


def fetch_news_for_tickers(symbols: list[str], limit_per_ticker: int = 6) -> list[dict]:
    items_by_url: dict[str, dict] = {}

    for symbol in symbols:
        try:
            raw_items = yf.Ticker(symbol).news or []
        except Exception:
            continue

        for raw in raw_items[:limit_per_ticker]:
            content = raw.get("content", raw)
            url = (content.get("canonicalUrl") or {}).get("url") or (
                content.get("clickThroughUrl") or {}
            ).get("url")
            title = content.get("title")
            if not url or not title:
                continue

            published_at = _parse_pub_date(content.get("pubDate"))
            provider = (content.get("provider") or {}).get("displayName", "")

            if url not in items_by_url:
                items_by_url[url] = {
                    "title": title,
                    "summary": content.get("summary") or "",
                    "source": provider,
                    "url": url,
                    "published_at": published_at,
                    "tickers": set(),
                }
            items_by_url[url]["tickers"].add(symbol)

    return sorted(items_by_url.values(), key=lambda i: i["published_at"], reverse=True)


def _parse_pub_date(value) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def fetch_economic_calendar(country: str = "USD") -> list[dict]:
    """
    Calendario económico semanal (fuente gratuita, sin API key: el feed
    público que usa el widget de ForexFactory). Solo se devuelven eventos
    de impacto medio y alto (2 y 3 estrellas) para el país indicado.
    """
    response = requests.get(CALENDAR_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    raw_events = response.json()

    events = []
    for item in raw_events:
        if item.get("country") != country:
            continue
        impact = item.get("impact")
        if impact not in RELEVANT_IMPACTS:
            continue

        event_time = _parse_event_time(item.get("date"))
        if event_time is None:
            continue

        title = (item.get("title") or "").strip()
        if not title:
            continue

        events.append({
            "title": title,
            "country": country,
            "event_time": event_time,
            "impact": CALENDAR_IMPACT_MAP[impact],
            "forecast": item.get("forecast") or "",
            "previous": item.get("previous") or "",
            "actual": item.get("actual") or "",
        })

    return sorted(events, key=lambda e: e["event_time"])


def _parse_event_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
