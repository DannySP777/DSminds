from django.http import HttpResponse
from django.shortcuts import redirect, render

from .charts import DEFAULT_INTERVAL, INTERVALS, build_mini_chart, build_price_chart
from .fundamentals import get_fundamentals
from .indices import get_market_indices
from .models import ScanResult
from .search import resolve_symbol


# Opciones fijas del filtro "precio menor a" (dropdown, no texto libre).
PRICE_LT_OPTIONS = [10, 30, 50, 100, 500, 1000, 10000]

# Bolsas disponibles en el filtro — el valor debe calzar exactamente con
# lo que guarda ScanResult.exchange (viene de fullExchangeName en
# yfinance). "S&P 500" no está aquí porque es un índice, no una bolsa:
# Yahoo Finance no expone por acción si pertenece al S&P 500, haría
# falta una lista de constituyentes mantenida aparte.
EXCHANGE_OPTIONS = [
    ("Nasdaq", "NASDAQ"),
    ("NYSE", "Nueva York (NYSE)"),
    ("Tokyo", "Tokio"),
    ("London", "Londres"),
    ("Frankfurt", "Fráncfort"),
    ("Toronto", "Toronto"),
    ("HKSE", "Hong Kong"),
]

# (parámetro en la URL, campo del modelo, operador) — filtros numéricos
# simples de "mín."/"máx." que se aplican directo sobre ScanResult.
NUMERIC_FILTER_FIELDS = [
    ("price_lt", "price", "lt"),
    ("rsi_min", "rsi", "gte"),
    ("rsi_max", "rsi", "lte"),
    ("rel_vol_min", "relative_volume", "gte"),
    ("rs_min", "relative_strength", "gte"),
    ("target_min", "target_price", "gte"),
    ("target_max", "target_price", "lte"),
    ("score_min", "score", "gte"),
    ("pe_min", "trailing_pe", "gte"),
    ("pe_max", "trailing_pe", "lte"),
    ("peg_min", "peg_ratio", "gte"),
    ("peg_max", "peg_ratio", "lte"),
    ("debt_max", "debt_to_equity", "lte"),
]
# Market cap se escribe en millones de USD en el formulario, pero se
# guarda en dólares crudos — necesita su propia conversión.
MARKET_CAP_FILTER_FIELDS = [
    ("cap_min", "market_cap", "gte"),
    ("cap_max", "market_cap", "lte"),
]


def home(request):
    filters = {}
    for param, _field, _op in NUMERIC_FILTER_FIELDS + MARKET_CAP_FILTER_FIELDS:
        filters[param] = request.GET.get(param, "").strip()
    filters["breakout"] = request.GET.get("breakout", "")
    filters["tendencia"] = request.GET.get("tendencia", "")
    filters["exchange"] = request.GET.get("exchange", "")
    filters_active = any(filters.values())

    latest = ScanResult.objects.select_related("ticker").first()
    resultados = []
    if latest:
        qs = ScanResult.objects.select_related("ticker").filter(date=latest.date)

        for param, field, op in NUMERIC_FILTER_FIELDS:
            raw = filters[param]
            if raw:
                try:
                    qs = qs.filter(**{f"{field}__{op}": float(raw)})
                except ValueError:
                    pass

        for param, field, op in MARKET_CAP_FILTER_FIELDS:
            raw = filters[param]
            if raw:
                try:
                    qs = qs.filter(**{f"{field}__{op}": float(raw) * 1_000_000})
                except ValueError:
                    pass

        if filters["breakout"] == "si":
            qs = qs.filter(breakout=True)
        elif filters["breakout"] == "no":
            qs = qs.filter(breakout=False)

        if filters["tendencia"] == "alcista":
            qs = qs.filter(above_ma200=True)
        elif filters["tendencia"] == "bajista":
            qs = qs.filter(above_ma200=False)

        if filters["exchange"] == "Nasdaq":
            # Agrupa las variantes de Nasdaq (NasdaqGS, NasdaqGM, NasdaqCM).
            qs = qs.filter(exchange__startswith="Nasdaq")
        elif filters["exchange"]:
            qs = qs.filter(exchange=filters["exchange"])

        resultados = list(qs)

    selected_symbol = resultados[0].ticker.symbol if resultados else None
    selected_chart = build_price_chart(selected_symbol, DEFAULT_INTERVAL) if selected_symbol else None
    selected_fundamentals = get_fundamentals(selected_symbol) if selected_symbol else None

    return render(request, "scanner/home.html", {
        "resultados": resultados,
        "filters": filters,
        "filters_active": filters_active,
        "indices": get_market_indices(),
        "intervals": INTERVALS,
        "price_lt_options": PRICE_LT_OPTIONS,
        "exchange_options": EXCHANGE_OPTIONS,
        "selected_symbol": selected_symbol,
        "selected_chart": selected_chart,
        "selected_interval": DEFAULT_INTERVAL,
        "selected_fundamentals": selected_fundamentals,
    })


def ticker_detail(request, symbol):
    symbol = symbol.upper()
    interval = request.GET.get("interval", DEFAULT_INTERVAL)
    if interval not in INTERVALS:
        interval = DEFAULT_INTERVAL

    chart = build_price_chart(symbol, interval)
    fundamentals = get_fundamentals(symbol)
    latest_result = (
        ScanResult.objects.select_related("ticker")
        .filter(ticker__symbol=symbol)
        .order_by("-date")
        .first()
    )

    return render(request, "scanner/ticker_detail.html", {
        "symbol": symbol,
        "chart": chart,
        "interval": interval,
        "intervals": INTERVALS,
        "latest_result": latest_result,
        "fundamentals": fundamentals,
    })


def ticker_chart_panel(request, symbol):
    """Fragmento AJAX: solo el panel de gráfica, para el dashboard del scanner."""
    symbol = symbol.upper()
    interval = request.GET.get("interval", DEFAULT_INTERVAL)
    if interval not in INTERVALS:
        interval = DEFAULT_INTERVAL

    chart = build_price_chart(symbol, interval)
    return render(request, "scanner/partials/chart_panel.html", {
        "symbol": symbol,
        "chart": chart,
        "interval": interval,
        "intervals": INTERVALS,
    })


def ticker_indicators_panel(request, symbol):
    """Fragmento AJAX: solo el panel de indicadores, para el dashboard del scanner."""
    symbol = symbol.upper()
    fundamentals = get_fundamentals(symbol)
    return render(request, "scanner/partials/indicators_panel.html", {
        "symbol": symbol,
        "fundamentals": fundamentals,
    })


def ticker_search(request):
    query = request.GET.get("q", "")
    symbol = resolve_symbol(query)
    if not symbol:
        return redirect("scanner-home")
    return redirect("ticker-detail", symbol=symbol)


def ticker_mini_chart(request, symbol):
    symbol = symbol.upper()
    chart = build_mini_chart(symbol)
    if chart["error"]:
        return HttpResponse(
            f'<p class="mini-chart-error">{chart["error"]}</p>'
        )
    return HttpResponse(chart["html"])
