"""
scanner/indices.py

Métricas rápidas de los principales índices/activos de referencia
(Nasdaq, S&P 500, Dow Jones, oro, petróleo) para mostrar en el panel
de "índices y alertas" del dashboard del scanner. Usa `fast_info` de
yfinance, mucho más liviano que descargar histórico completo, y arma
un semáforo/medidor (reutilizando el mismo componente visual de
partials/gauge.html) según qué tan fuerte fue el movimiento del día.
"""
import yfinance as yf
from django.core.cache import cache

INDICES_TTL = 300

INDEX_TICKERS = [
    {"symbol": "^IXIC", "label": "Nasdaq"},
    {"symbol": "^GSPC", "label": "S&P 500"},
    {"symbol": "^DJI", "label": "Dow Jones"},
    {"symbol": "GC=F", "label": "Oro"},
    {"symbol": "CL=F", "label": "Petróleo"},
]

# Semáforo del cambio diario: escala -3% a +3%, con zona neutral entre
# -1% y +1%. Fuera de ahí ya es un movimiento notable para un índice.
GAUGE_MIN, GAUGE_MAX = -3, 3
GAUGE_LOW, GAUGE_HIGH = -1, 1


def get_market_indices() -> list[dict]:
    cached = cache.get("scanner:indices")
    if cached is not None:
        return cached

    results = [_fetch_one(item) for item in INDEX_TICKERS]
    cache.set("scanner:indices", results, INDICES_TTL)
    return results


def _fetch_one(item: dict) -> dict:
    try:
        fast_info = yf.Ticker(item["symbol"]).fast_info
        price = fast_info["lastPrice"]
        previous_close = fast_info["previousClose"]
        change_pct = round((price / previous_close - 1) * 100, 2) if previous_close else None
        return {
            "label": item["label"],
            "price": round(price, 2),
            "change_pct": change_pct,
            "gauge": _gauge(change_pct),
        }
    except Exception:
        return {
            "label": item["label"],
            "price": None,
            "change_pct": None,
            "gauge": _gauge(None),
        }


def _gauge(change_pct) -> dict:
    span = GAUGE_MAX - GAUGE_MIN
    zones = [
        ("bad", round((GAUGE_LOW - GAUGE_MIN) / span * 100, 1)),
        ("warning", round((GAUGE_HIGH - GAUGE_LOW) / span * 100, 1)),
        ("good", round((GAUGE_MAX - GAUGE_HIGH) / span * 100, 1)),
    ]

    if change_pct is None:
        return {"level": "unknown", "position": None, "zones": zones}

    if change_pct <= GAUGE_LOW:
        level = "bad"
    elif change_pct < GAUGE_HIGH:
        level = "warning"
    else:
        level = "good"

    clamped = max(GAUGE_MIN, min(GAUGE_MAX, change_pct))
    position = round((clamped - GAUGE_MIN) / span * 100, 1)

    return {"level": level, "position": position, "zones": zones}
