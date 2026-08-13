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


def search_candidates(query: str) -> list[dict]:
    """
    Lista de acciones candidatas para el autocompletado del buscador
    "agregar al scanner" — a diferencia de resolve_symbol, no elige una
    sola: devuelve varias para que el usuario seleccione la correcta
    (ej. "NOK" podría ser Nokia u otra empresa con ticker parecido).
    """
    query = (query or "").strip()
    if not query:
        return []

    cache_key = f"scanner:search-candidates:{query.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        quotes = yf.Search(query, max_results=8).quotes
    except Exception:
        quotes = []

    candidates = []
    seen = set()
    for q in quotes:
        if q.get("quoteType") != "EQUITY":
            continue
        symbol = (q.get("symbol") or "").upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        candidates.append({
            "symbol": symbol,
            "name": q.get("shortname") or q.get("longname") or "",
            "exchange": q.get("exchDisp") or q.get("exchange") or "",
        })

    cache.set(cache_key, candidates, SEARCH_TTL)
    return candidates
