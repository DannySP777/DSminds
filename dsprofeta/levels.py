"""
dsprofeta/levels.py

Detección de soportes y resistencias "institucionales" sobre velas
diarias: un pivote (mínimo o máximo local, más significativo que el
ruido de una sola vela) que el precio respetó más de una vez en el
último mes es, en la práctica, el nivel que la mayoría de la literatura
técnica llama "soporte/resistencia institucional" — zonas donde volúmenes
grandes repetidamente frenaron o revirtieron el precio, sin necesidad de
datos de order flow que yfinance no expone.

Regla determinista, sin IA: un pivote low/high es una vela cuyo low/high
es el mínimo/máximo dentro de una ventana de `PIVOT_WINDOW` velas a cada
lado. Los pivotes cercanos entre sí (dentro de `CLUSTER_PCT` del precio)
se agrupan en un solo nivel, promediando el precio y sumando los
"toques" — más toques = nivel más significativo.
"""
from .models import PriceBar

PIVOT_WINDOW = 2
CLUSTER_PCT = 0.006  # 0.6%: precios pivote a menos de esta distancia relativa se consideran el mismo nivel
LOOKBACK_DAYS = 22  # ~1 mes de ruedas hábiles
MAX_LEVELS = 3


def _find_pivots(values, window, mode):
    """`values` en orden cronológico. Devuelve los índices que son pivote
    (mínimo local si mode="low", máximo local si mode="high") dentro de
    `window` velas a cada lado — se excluyen los bordes, que no tienen
    suficiente contexto a ambos lados para confirmar el pivote."""
    pivots = []
    for i in range(window, len(values) - window):
        segment = values[i - window: i + window + 1]
        if mode == "low" and values[i] == min(segment):
            pivots.append(i)
        elif mode == "high" and values[i] == max(segment):
            pivots.append(i)
    return pivots


def _cluster_levels(prices, reference_price, max_levels=MAX_LEVELS):
    """Agrupa precios de pivote cercanos entre sí en niveles únicos,
    ordenados por cantidad de toques (más toques primero) y devuelve
    como máximo `max_levels`."""
    if not prices:
        return []

    clusters = []  # cada cluster: {"prices": [...]}
    for price in sorted(prices):
        placed = False
        for cluster in clusters:
            cluster_avg = sum(cluster["prices"]) / len(cluster["prices"])
            if reference_price and abs(price - cluster_avg) / reference_price <= CLUSTER_PCT:
                cluster["prices"].append(price)
                placed = True
                break
        if not placed:
            clusters.append({"prices": [price]})

    levels = [
        {"price": round(sum(c["prices"]) / len(c["prices"]), 5), "touches": len(c["prices"])}
        for c in clusters
    ]
    levels.sort(key=lambda lv: (-lv["touches"], abs(lv["price"] - reference_price) if reference_price else 0))
    return levels[:max_levels]


def detect_levels(asset, lookback_days=LOOKBACK_DAYS, max_levels=MAX_LEVELS, pivot_window=PIVOT_WINDOW):
    """
    Soportes y resistencias del último mes de velas diarias (D1) de
    `asset`. Devuelve {"supports": [...], "resistances": [...]}, cada
    nivel como {"price": float, "touches": int}, ordenados del más
    significativo (más toques) al menos, y como máximo `max_levels` cada
    uno. Vacío si no hay suficiente historial diario todavía. Los
    parámetros extra los usa la pantalla Trading Análisis (ventana de ~3
    meses y más niveles que el resumen de un mes de Trading con IA).
    """
    bars = list(
        PriceBar.objects.filter(asset=asset, timeframe="1d")
        .order_by("-timestamp")[:lookback_days]
    )
    bars.reverse()
    if len(bars) < (pivot_window * 2 + 3):
        return {"supports": [], "resistances": []}

    lows = [float(b.low) for b in bars]
    highs = [float(b.high) for b in bars]
    current_price = float(bars[-1].close)

    low_pivots = [lows[i] for i in _find_pivots(lows, pivot_window, "low")]
    high_pivots = [highs[i] for i in _find_pivots(highs, pivot_window, "high")]

    # Un soporte por debajo del precio actual y una resistencia por
    # encima son los únicos que sirven como referencia práctica (un
    # "soporte" por encima del precio actual ya fue superado, no protege
    # nada). Si el pivote quedó del lado "equivocado" igual se conserva
    # el algoritmo simple: se filtra acá, no en la detección.
    supports = _cluster_levels([p for p in low_pivots if p <= current_price], current_price, max_levels)
    resistances = _cluster_levels([p for p in high_pivots if p >= current_price], current_price, max_levels)

    return {"supports": supports, "resistances": resistances}
