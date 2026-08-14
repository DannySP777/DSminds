from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from config.translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations

from .charts import DEFAULT_INTERVAL, INTERVALS, build_mini_chart, build_price_chart
from .fundamentals import get_fundamentals
from .indices import get_market_indices
from .models import ScanResult, Ticker
from .search import resolve_symbol, search_candidates
from .services import save_scan_results


def _get_lang(request):
    lang = request.COOKIES.get("site_lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


# Opciones fijas del filtro de precio, por rango (dropdown, no texto
# libre). (clave en la URL, mínimo o None, máximo o None, etiqueta).
PRICE_RANGE_OPTIONS = [
    ("lt10", None, 10, "Menor a $10"),
    ("11-30", 11, 30, "$11 a $30"),
    ("31-50", 31, 50, "$31 a $50"),
    ("51-100", 51, 100, "$51 a $100"),
    ("101-500", 101, 500, "$101 a $500"),
    ("gt500", 500, None, "Mayores a $500"),
]
PRICE_RANGE_BOUNDS = {key: (lo, hi) for key, lo, hi, _label in PRICE_RANGE_OPTIONS}

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
# Acotados a propósito a lo que muestra la tabla simplificada del
# scanner (score, precio, P/E, PEG, market cap, volumen, precio
# objetivo) — sin indicadores técnicos avanzados que no se muestran ahí.
NUMERIC_FILTER_FIELDS = [
    ("rel_vol_min", "relative_volume", "gte"),
    ("target_min", "target_price", "gte"),
    ("target_max", "target_price", "lte"),
    ("score_min", "score", "gte"),
    ("pe_min", "trailing_pe", "gte"),
    ("pe_max", "trailing_pe", "lte"),
    ("peg_min", "peg_ratio", "gte"),
    ("peg_max", "peg_ratio", "lte"),
]
# Market cap se escribe en millones de USD en el formulario, pero se
# guarda en dólares crudos — necesita su propia conversión.
MARKET_CAP_FILTER_FIELDS = [
    ("cap_min", "market_cap", "gte"),
    ("cap_max", "market_cap", "lte"),
]

# El scanner siempre muestra por defecto el top N por score (ya sea
# sobre el universo completo o sobre el resultado de aplicar filtros)
# en vez de la lista completa — evita abrumar con una tabla larga.
# El usuario puede pedir "ver todas" con ?show_all=1, que se calcula
# siempre sobre el conjunto YA filtrado, nunca antes de filtrar.
DEFAULT_RESULT_LIMIT = 10


def home(request):
    lang = _get_lang(request)
    filters = {}
    for param, _field, _op in NUMERIC_FILTER_FIELDS + MARKET_CAP_FILTER_FIELDS:
        filters[param] = request.GET.get(param, "").strip()
    filters["exchange"] = request.GET.get("exchange", "")
    filters["price_range"] = request.GET.get("price_range", "")
    filters_active = any(filters.values())
    show_all = request.GET.get("show_all") == "1"

    # Los tickers agregados manualmente (ver add_ticker) se calculan
    # apenas se agregan, con la fecha de hoy — pero el resto del universo
    # recién se re-escanea en el cron nocturno. Si tomáramos "la fecha
    # del ScanResult más reciente" a secas, un ticker agregado hoy
    # dejaría fuera a los demás (que siguen fechados ayer). Por eso el
    # "lote" del día se calcula ignorando los agregados manualmente, y
    # estos se muestran aparte, siempre fijados arriba de la tabla.
    batch_latest = (
        ScanResult.objects.filter(ticker__added_manually=False)
        .order_by("-date")
        .first()
    )
    batch_date = batch_latest.date if batch_latest else None

    added_results = []
    for t in Ticker.objects.filter(added_manually=True, is_active=True).order_by("-added_at"):
        sr = ScanResult.objects.select_related("ticker").filter(ticker=t).order_by("-date").first()
        if sr:
            sr.is_added_row = True
            added_results.append(sr)

    resultados = []
    total_scanned = 0
    matched_count = 0
    if batch_date:
        qs = ScanResult.objects.select_related("ticker").filter(date=batch_date, ticker__added_manually=False)
        total_scanned = qs.count()

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

        price_bounds = PRICE_RANGE_BOUNDS.get(filters["price_range"])
        if price_bounds:
            lo, hi = price_bounds
            if lo is not None:
                qs = qs.filter(price__gte=lo)
            if hi is not None:
                qs = qs.filter(price__lte=hi)

        if filters["exchange"] == "Nasdaq":
            # Agrupa las variantes de Nasdaq (NasdaqGS, NasdaqGM, NasdaqCM).
            qs = qs.filter(exchange__startswith="Nasdaq")
        elif filters["exchange"]:
            qs = qs.filter(exchange=filters["exchange"])

        # El score ya viene calculado por run_scan y el queryset está
        # ordenado -score (Meta.ordering de ScanResult), así que el
        # top N sobre el conjunto filtrado sale gratis con un slice.
        matched_count = qs.count()

        if not show_all:
            qs = qs[:DEFAULT_RESULT_LIMIT]

        resultados = list(qs)

    # Los agregados manualmente van siempre primero, sin importar
    # filtros ni paginación — son un "watchlist" fijado, no parte del
    # top N del scan por lotes.
    added_symbols = {r.ticker.symbol for r in added_results}
    resultados = added_results + [r for r in resultados if r.ticker.symbol not in added_symbols]

    truncated = matched_count > DEFAULT_RESULT_LIMIT and not show_all

    show_all_params = request.GET.copy()
    show_all_params["show_all"] = "1"
    show_all_qs = show_all_params.urlencode()

    show_less_params = request.GET.copy()
    show_less_params.pop("show_all", None)
    show_less_qs = show_less_params.urlencode()

    selected_symbol = resultados[0].ticker.symbol if resultados else None
    selected_chart = build_price_chart(selected_symbol, DEFAULT_INTERVAL, lang) if selected_symbol else None
    selected_fundamentals = get_fundamentals(selected_symbol, lang) if selected_symbol else None

    return render(request, "scanner/home.html", {
        "resultados": resultados,
        "filters": filters,
        "filters_active": filters_active,
        "total_scanned": total_scanned,
        "matched_count": matched_count,
        "default_result_limit": DEFAULT_RESULT_LIMIT,
        "truncated": truncated,
        "show_all": show_all,
        "show_all_qs": show_all_qs,
        "show_less_qs": show_less_qs,
        "indices": get_market_indices(),
        "intervals": INTERVALS,
        "price_range_options": PRICE_RANGE_OPTIONS,
        "exchange_options": EXCHANGE_OPTIONS,
        "selected_symbol": selected_symbol,
        "selected_chart": selected_chart,
        "selected_interval": DEFAULT_INTERVAL,
        "selected_fundamentals": selected_fundamentals,
    })


def ticker_detail(request, symbol):
    lang = _get_lang(request)
    symbol = symbol.upper()
    interval = request.GET.get("interval", DEFAULT_INTERVAL)
    if interval not in INTERVALS:
        interval = DEFAULT_INTERVAL

    chart = build_price_chart(symbol, interval, lang)
    fundamentals = get_fundamentals(symbol, lang)
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
    lang = _get_lang(request)
    symbol = symbol.upper()
    interval = request.GET.get("interval", DEFAULT_INTERVAL)
    if interval not in INTERVALS:
        interval = DEFAULT_INTERVAL

    chart = build_price_chart(symbol, interval, lang)
    return render(request, "scanner/partials/chart_panel.html", {
        "symbol": symbol,
        "chart": chart,
        "interval": interval,
        "intervals": INTERVALS,
    })


def ticker_indicators_panel(request, symbol):
    """Fragmento AJAX: solo el panel de indicadores, para el dashboard del scanner."""
    lang = _get_lang(request)
    symbol = symbol.upper()
    fundamentals = get_fundamentals(symbol, lang)
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
    lang = _get_lang(request)
    symbol = symbol.upper()
    chart = build_mini_chart(symbol, lang)
    if chart["error"]:
        return HttpResponse(
            f'<p class="mini-chart-error">{chart["error"]}</p>'
        )
    return HttpResponse(chart["html"])


def ticker_autocomplete(request):
    """JSON para el buscador de 'agregar acción al scanner' (home.html)."""
    query = request.GET.get("q", "")
    if len(query.strip()) < 2:
        return JsonResponse({"results": []})
    return JsonResponse({"results": search_candidates(query)})


@require_POST
def add_ticker(request):
    """
    Agrega un ticker nuevo (elegido en el autocompletado de home.html)
    al universo del scanner: lo activa en la tabla Ticker (para que
    quede incluido en los scans programados de ahí en adelante, ver
    run_scan.py) y calcula su ScanResult de hoy en el momento, para que
    aparezca de inmediato en vez de esperar al próximo scan diario.
    """
    lang = _get_lang(request)
    T = get_translations(lang)
    symbol = (request.POST.get("symbol") or "").strip().upper()

    if not symbol:
        messages.error(request, T["add_ticker_missing"])
        return redirect("scanner-home")

    fundamentals = get_fundamentals(symbol, lang)
    if not fundamentals.get("has_data"):
        messages.error(request, T["add_ticker_not_found"].format(symbol=symbol))
        return redirect("scanner-home")

    ticker, _ = Ticker.objects.get_or_create(symbol=symbol)
    ticker.is_active = True
    ticker.added_manually = True
    ticker.added_at = timezone.now()
    ticker.save(update_fields=["is_active", "added_manually", "added_at"])

    save_scan_results([symbol])

    messages.success(request, T["add_ticker_success"].format(symbol=symbol))
    return redirect("scanner-home")


@require_POST
def remove_ticker(request, symbol):
    """Quita un ticker agregado manualmente (ver add_ticker) del scanner."""
    lang = _get_lang(request)
    T = get_translations(lang)
    symbol = symbol.upper()

    Ticker.objects.filter(symbol=symbol, added_manually=True).update(is_active=False)

    messages.success(request, T["remove_ticker_success"].format(symbol=symbol))
    return redirect("scanner-home")
