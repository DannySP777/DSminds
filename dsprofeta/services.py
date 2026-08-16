"""
Servicios de datos de DSprofeta: descarga de precios (yfinance),
calendario económico y noticias (Finnhub), y resolución de predicciones
contra el precio real observado.
"""
import logging
from datetime import timezone as dt_timezone

import pandas as pd
import requests
import yfinance as yf
from django.conf import settings
from django.utils import timezone as dj_timezone

from .charts import invalidate_prediction_chart
from .models import EconomicEvent, NewsHeadline, PriceBar, Prediction

logger = logging.getLogger(__name__)

# yfinance no tiene intervalo nativo "4h": se pide "1h" y se agrupa acá.
YF_INTERVAL = {"15m": "15m", "1h": "1h", "4h": "1h", "1d": "1d", "1w": "1wk"}
# Límites de historial intradía que impone Yahoo Finance, no nosotros.
YF_PERIOD = {"15m": "60d", "1h": "730d", "4h": "730d", "1d": "5y", "1w": "10y"}

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Palabras clave usadas para etiquetar qué activo(s) menciona cada
# titular de noticias (Finnhub "general" no viene pre-filtrado por
# activo). No es análisis de sentimiento, solo detección de menciones.
ASSET_KEYWORDS = {
    "NDX100": ["nasdaq", "tech stocks", "technology stocks"],
    "GOLD": ["gold", "bullion", "precious metal"],
    "EURUSD": ["euro", "ecb", "dollar", "fed rate"],
    "SPX500": ["s&p 500", "s&p500", "wall street"],
}


def _download_bars(asset, timeframe):
    yf_interval = YF_INTERVAL[timeframe]
    period = YF_PERIOD[timeframe]
    data = yf.download(
        asset.yfinance_symbol, period=period, interval=yf_interval,
        progress=False, auto_adjust=True,
    )
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    if data.empty:
        return data

    if timeframe == "4h":
        data = data.resample("4h").agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
        }).dropna(subset=["Open"])

    return data


def sync_prices(asset, timeframe):
    """Descarga velas de yfinance y las guarda/actualiza en PriceBar."""
    data = _download_bars(asset, timeframe)
    if data.empty:
        logger.warning("Sin datos de yfinance para %s (%s)", asset.symbol, timeframe)
        return 0

    saved = 0
    for ts, row in data.iterrows():
        if pd.isna(row["Close"]):
            continue
        ts = ts.to_pydatetime()
        if dj_timezone.is_naive(ts):
            ts = dj_timezone.make_aware(ts, dt_timezone.utc)
        PriceBar.objects.update_or_create(
            asset=asset, timeframe=timeframe, timestamp=ts,
            defaults={
                "open": round(float(row["Open"]), 5),
                "high": round(float(row["High"]), 5),
                "low": round(float(row["Low"]), 5),
                "close": round(float(row["Close"]), 5),
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else None,
            },
        )
        saved += 1
    return saved


def _finnhub_get(path, params):
    api_key = getattr(settings, "FINNHUB_API_KEY", "") or ""
    if not api_key:
        logger.warning("FINNHUB_API_KEY no configurada — se omite %s", path)
        return None
    params = {**params, "token": api_key}
    try:
        response = requests.get(f"{FINNHUB_BASE_URL}{path}", params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        logger.exception("Finnhub %s falló", path)
        return None


def sync_economic_calendar(days_back=7, days_ahead=14):
    now = dj_timezone.now()
    params = {
        "from": (now - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d"),
        "to": (now + pd.Timedelta(days=days_ahead)).strftime("%Y-%m-%d"),
    }
    payload = _finnhub_get("/calendar/economic", params)
    if not payload:
        return 0

    saved = 0
    for item in payload.get("economicCalendar", []):
        event_time_raw = item.get("time")
        if not event_time_raw:
            continue
        event_time = pd.to_datetime(event_time_raw, utc=True, errors="coerce")
        if pd.isna(event_time):
            continue
        title = (item.get("event") or "").strip()
        if not title:
            continue
        EconomicEvent.objects.update_or_create(
            event_time=event_time.to_pydatetime(),
            title=title,
            country=item.get("country", "") or "",
            defaults={
                "impact": item.get("impact") or EconomicEvent.Impact.LOW,
                "actual": item.get("actual"),
                "forecast": item.get("estimate"),
                "previous": item.get("prev"),
            },
        )
        saved += 1
    return saved


def sync_market_news(limit=200):
    payload = _finnhub_get("/news", {"category": "general"})
    if not payload:
        return 0

    saved = 0
    for item in payload[:limit]:
        published_ts = item.get("datetime")
        headline = (item.get("headline") or "").strip()
        if not published_ts or not headline:
            continue
        published_at = pd.to_datetime(published_ts, unit="s", utc=True).to_pydatetime()
        text = f"{headline} {item.get('summary', '')}".lower()
        matched = [symbol for symbol, keywords in ASSET_KEYWORDS.items() if any(k in text for k in keywords)]

        NewsHeadline.objects.update_or_create(
            published_at=published_at,
            headline=headline[:300],
            defaults={
                "related_symbols": ",".join(matched),
                "source": item.get("source", "") or "",
            },
        )
        saved += 1
    return saved


def resolve_predictions():
    """Completa actual_close en predicciones cuya target_time ya pasó."""
    pending = Prediction.objects.filter(actual_close__isnull=True, target_time__lte=dj_timezone.now())
    resolved = 0
    for prediction in pending:
        bar = (
            PriceBar.objects.filter(
                asset=prediction.asset,
                timeframe=prediction.timeframe,
                timestamp__gte=prediction.target_time,
            )
            .order_by("timestamp")
            .first()
        )
        if bar is None:
            continue
        prediction.actual_close = bar.close
        prediction.resolved_at = dj_timezone.now()
        prediction.save(update_fields=["actual_close", "resolved_at"])
        invalidate_prediction_chart(prediction.asset, prediction.timeframe)
        resolved += 1
    return resolved
