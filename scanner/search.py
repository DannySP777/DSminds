"""
scanner/search.py

Resuelve lo que el usuario escribe en el buscador (símbolo o nombre de
la empresa, ej. "AAPL" o "Tesla") a un ticker válido, usando la
búsqueda de Yahoo Finance.
"""
import yfinance as yf
from django.core.cache import cache

SEARCH_TTL = 600


def resolve_symbol(query: str) -> str:
    query = (query or "").strip()
    if not query:
        return ""

    cache_key = f"scanner:search:{query.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    symbol = _search_symbol(query)
    cache.set(cache_key, symbol, SEARCH_TTL)
    return symbol


def _search_symbol(query: str) -> str:
    try:
        quotes = yf.Search(query, max_results=8).quotes
    except Exception:
        quotes = []

    equities = [q for q in quotes if q.get("quoteType") == "EQUITY"]
    us_equities = [q for q in equities if "." not in (q.get("symbol") or "")]

    for candidates in (us_equities, equities, quotes):
        if candidates:
            return candidates[0]["symbol"].upper()

    return query.upper().replace(" ", "")
