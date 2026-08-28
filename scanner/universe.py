"""
Descubre y clasifica el universo ampliado de acciones para la vista
"sistema solar" del scanner (tres grupos: penny/monster/standard), en
pasadas de costo creciente — mismo criterio de tiering que ya usa el
resto del scanner (indices.py: fast_info barato; fundamentals.py:
.info medio; services.py: descarga OHLCV cara):

1. discover_group_candidates() — un yf.EquityQuery por grupo (precio y
   market cap ya vienen filtrados por Yahoo), ordenado por volumen del
   día. Una sola llamada de red por grupo, sin .info por símbolo.
2. bucket_and_validate() — revalida en Python lo que ya trae el quote
   (precio/market cap/bolsa), por si los datos cambiaron entre el
   momento del query y el de lectura. Sin red.
3. enrich_and_rank() — SOLO sobre un shortlist acotado por grupo: pega
   target_mean_price vía fundamentals.get_fundamentals() (mismo fetch
   que ya paga el scan diario de 63 tickers, ahora escalado a un
   universo más grande pero con tope duro) y calcula el ranking
   compuesto (percentile-rank de upside% + percentile-rank de volumen
   relativo, promediados).

Campos de nombre de columna del screener (regularMarketPrice,
marketCap, exchange, regularMarketVolume, averageDailyVolume3Month,
intradayprice, intradaymarketcap, dayvolume) verificados en vivo contra
la versión instalada de yfinance (1.5.2) — no son parte de la API
pública documentada de Yahoo, así que un cambio del lado de Yahoo puede
romperlos; cada llamada de red está aislada en su propio try/except
para que un grupo que falla no tumbe a los otros dos.
"""
import logging

import yfinance as yf

from .fundamentals import get_fundamentals
from .models import ScanResult

logger = logging.getLogger(__name__)

PENNY_PRICE_MAX = 2.0
MONSTER_MARKET_CAP_MIN = 100e9  # 100B — punto de partida; bajar si --dry-run muestra <20 candidatos

PENNY_TARGET_COUNT = 20
MONSTER_TARGET_COUNT = 20
STANDARD_TARGET_COUNT = 20

# Cuántos candidatos por grupo (ya ordenados por volumen/market cap por
# Yahoo) se enriquecen con fundamentals.get_fundamentals() — el paso
# caro del pipeline. Acotado para que el costo total de una corrida
# esté cerca del scan legacy de 63 tickers, no de miles.
PENNY_SHORTLIST = 150
MONSTER_SHORTLIST = 40
STANDARD_SHORTLIST = 150

# NMS/NGM/NCM = Nasdaq Global Select/Global/Capital Market, NYQ = NYSE,
# ASE = NYSE American — igual criterio "solo USD, sin conversión de
# moneda" que scanner/services.py::DEFAULT_TICKERS.
US_EXCHANGES = ["NMS", "NYQ", "NGM", "NCM", "ASE"]


SCREENER_PAGE_SIZE = 25  # el endpoint de Yahoo ignora `count` por encima de esto y devuelve 25 igual


def _run_query(query, count, sort_field):
    """
    yf.screen() acepta `count` pero el endpoint de Yahoo lo ignora y
    devuelve como mucho 25 quotes por llamada (verificado en vivo) —
    para juntar más hace falta paginar con `offset`. Para de paginar
    al llegar a `count` o al agotar `total` (o tras un error de red, sin
    tumbar lo ya juntado).
    """
    quotes = []
    offset = 0
    while len(quotes) < count:
        try:
            resp = yf.screen(query, offset=offset, count=SCREENER_PAGE_SIZE, sortField=sort_field, sortAsc=False)
        except Exception:
            logger.exception("universe: página de screener falló en offset=%s", offset)
            break

        page = resp.get("quotes", [])
        if not page:
            break
        quotes.extend(page)
        offset += SCREENER_PAGE_SIZE
        if offset >= (resp.get("total") or offset):
            break

    return quotes[:count]


def discover_group_candidates() -> dict[str, list[dict]]:
    """
    Un EquityQuery por grupo, ya acotado por precio/market cap del lado
    de Yahoo — devuelve los quotes crudos, ordenados por volumen del
    día (o market cap para "monster"). Un grupo que falla (rate limit,
    campo movido del lado de Yahoo) se loguea y queda vacío — no tumba
    a los otros dos.
    """
    candidates: dict[str, list[dict]] = {"penny": [], "monster": [], "standard": []}

    try:
        query = yf.EquityQuery("and", [
            yf.EquityQuery("lt", ["intradayprice", PENNY_PRICE_MAX]),
            yf.EquityQuery("is-in", ["exchange", *US_EXCHANGES]),
        ])
        candidates["penny"] = _run_query(query, PENNY_SHORTLIST, "dayvolume")
    except Exception:
        logger.exception("universe: query de penny stocks falló")

    try:
        query = yf.EquityQuery("and", [
            yf.EquityQuery("gte", ["intradaymarketcap", MONSTER_MARKET_CAP_MIN]),
            yf.EquityQuery("is-in", ["exchange", *US_EXCHANGES]),
        ])
        candidates["monster"] = _run_query(query, MONSTER_SHORTLIST, "intradaymarketcap")
    except Exception:
        logger.exception("universe: query de monster stocks falló")

    try:
        query = yf.EquityQuery("and", [
            yf.EquityQuery("gte", ["intradayprice", PENNY_PRICE_MAX]),
            yf.EquityQuery("lt", ["intradaymarketcap", MONSTER_MARKET_CAP_MIN]),
            yf.EquityQuery("is-in", ["exchange", *US_EXCHANGES]),
        ])
        candidates["standard"] = _run_query(query, STANDARD_SHORTLIST, "dayvolume")
    except Exception:
        logger.exception("universe: query de standard stocks falló")

    return candidates


def bucket_and_validate(candidates: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """
    Revalida en Python lo que cada quote ya trae (precio/market
    cap/bolsa) — sin red. Filtra símbolos sin datos utilizables y
    reclasifica cualquier quote que haya quedado en el bucket
    equivocado (el precio pudo moverse entre el momento del query y
    esta lectura). Dedupea por símbolo dentro de cada bucket.
    """
    buckets = {"penny": {}, "monster": {}, "standard": {}}

    for group, quotes in candidates.items():
        for quote in quotes:
            symbol = quote.get("symbol")
            price = quote.get("regularMarketPrice")
            market_cap = quote.get("marketCap")
            exchange = quote.get("exchange")
            if not symbol or not price or exchange not in US_EXCHANGES:
                continue

            quote["_symbol"] = symbol
            quote["_price"] = price
            quote["_market_cap"] = market_cap

            if price < PENNY_PRICE_MAX:
                real_group = "penny"
            elif market_cap and market_cap >= MONSTER_MARKET_CAP_MIN:
                real_group = "monster"
            else:
                real_group = "standard"

            buckets[real_group][symbol] = quote

    return {group: list(quotes.values()) for group, quotes in buckets.items()}


def _relative_volume_from_quote(quote: dict):
    volume = quote.get("regularMarketVolume")
    avg_volume = quote.get("averageDailyVolume3Month") or quote.get("averageDailyVolume10Day")
    if not volume or not avg_volume:
        return None
    return round(volume / avg_volume, 2)


def _percentile_ranks(entries: list[dict], key: str) -> dict:
    """
    Percentile-rank (0-100) de entries[i][key] contra las demás
    entradas del mismo grupo — None se excluye del cálculo (esa acción
    no compite en ese eje). Empates comparten el percentile promedio de
    su posición, convención estándar de percentile-rank.
    """
    valid = [(i, e[key]) for i, e in enumerate(entries) if e.get(key) is not None]
    if not valid:
        return {}
    if len(valid) == 1:
        return {valid[0][0]: 100.0}

    valid.sort(key=lambda pair: pair[1])
    n = len(valid)
    ranks = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and valid[j + 1][1] == valid[i][1]:
            j += 1
        avg_position = (i + j) / 2
        pct = avg_position / (n - 1) * 100
        for k in range(i, j + 1):
            ranks[valid[k][0]] = pct
        i = j + 1
    return ranks


def _rank_group(entries: list[dict], target_count: int) -> list[dict]:
    """
    composite = promedio del percentile-rank de upside% y del
    percentile-rank de volumen relativo, calculados por separado
    dentro de ESTE grupo (percentiles no tienen sentido mezclando
    penny con monster). Una entrada sin ninguno de los dos ejes se
    descarta (no hay nada sobre qué rankearla); con solo uno, el eje
    faltante cuenta como percentile 0 para esa entrada.
    """
    entries = [e for e in entries if e.get("_upside_pct") is not None or e.get("_relative_volume") is not None]
    upside_ranks = _percentile_ranks(entries, "_upside_pct")
    relvol_ranks = _percentile_ranks(entries, "_relative_volume")

    for i, e in enumerate(entries):
        e["_composite"] = round((upside_ranks.get(i, 0.0) + relvol_ranks.get(i, 0.0)) / 2, 2)

    entries.sort(key=lambda e: e["_composite"], reverse=True)
    top = entries[:target_count]
    for rank, e in enumerate(top, start=1):
        e["_rank"] = rank
    return top


def enrich_and_rank(bucketed: dict[str, list[dict]], lang: str = "es") -> dict[str, list[dict]]:
    shortlist_limits = {"penny": PENNY_SHORTLIST, "monster": MONSTER_SHORTLIST, "standard": STANDARD_SHORTLIST}
    target_counts = {"penny": PENNY_TARGET_COUNT, "monster": MONSTER_TARGET_COUNT, "standard": STANDARD_TARGET_COUNT}
    ranked = {}

    for group, quotes in bucketed.items():
        # Cada lista ya viene ordenada por lo que importa a ese grupo
        # (volumen del día para penny/standard, market cap para
        # monster) desde el propio EquityQuery — alcanza con recortar,
        # no hace falta reordenar.
        shortlisted = quotes[:shortlist_limits[group]]

        for quote in shortlisted:
            symbol = quote["_symbol"]
            try:
                fundamentals = get_fundamentals(symbol, lang, include_summary=False)
            except Exception:
                logger.exception("universe: get_fundamentals falló para %s", symbol)
                fundamentals = {}

            target = fundamentals.get("target_mean_price")
            current = fundamentals.get("current_price") or quote["_price"]
            quote["_upside_pct"] = (
                round((target / current - 1) * 100, 2) if target and current else None
            )
            quote["_relative_volume"] = _relative_volume_from_quote(quote)

        ranked[group] = _rank_group(shortlisted, target_counts[group])

    return ranked


def build_universe(lang: str = "es") -> dict[str, list[dict]]:
    candidates = discover_group_candidates()
    bucketed = bucket_and_validate(candidates)
    return enrich_and_rank(bucketed, lang)
