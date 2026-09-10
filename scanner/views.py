from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render

from config.translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations

from .charts import (
    DEFAULT_INTERVAL,
    INTERVALS,
    build_financials_chart,
    build_mini_chart,
    build_price_chart,
    build_top10_overview_chart,
)
from .commentary import build_ticker_commentary
from .fundamentals import get_fundamentals
from .indices import get_market_indices
from .models import ScanResult
from .search import resolve_symbol
from .services import build_all_group_summaries

TOP10_SIZE = 10


def _get_lang(request):
    # ?lang= manda sobre la cookie — debe resolver igual que
    # config.context_processors._resolve_lang, o T/LANG del layout queda
    # desincronizado del idioma que arma esta vista.
    lang = request.GET.get("lang") or request.COOKIES.get("site_lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def home(request):
    lang = _get_lang(request)
    T = get_translations(lang)

    # Top 10 del día: un solo ranking global por `score` (comparable entre
    # penny/monster/standard porque se calcula igual en ambos pipelines,
    # a diferencia de momentum_rank, que es un percentil solo comparable
    # dentro de su propio grupo — ver scanner/universe.py). is_active=True
    # respeta el opt-out ya usado para desactivar duplicados (ej. NOK).
    latest_date = ScanResult.objects.order_by("-date").values_list("date", flat=True).first()
    top10 = []
    if latest_date:
        top10 = list(
            ScanResult.objects.select_related("ticker")
            .filter(date=latest_date, ticker__is_active=True)
            .order_by("-score")[:TOP10_SIZE]
        )
    for r in top10:
        r.commentary = build_ticker_commentary(r, lang)

    top10_chart = build_top10_overview_chart(top10, lang) if top10 else None
    selected_symbol = top10[0].ticker.symbol if top10 else None
    selected_chart = build_price_chart(selected_symbol, DEFAULT_INTERVAL, lang) if selected_symbol else None
    selected_fundamentals = get_fundamentals(selected_symbol, lang) if selected_symbol else None
    selected_financials_chart = build_financials_chart(selected_symbol, lang) if selected_symbol else None
    group_summaries = build_all_group_summaries(lang)

    return render(request, "scanner/home.html", {
        "indices": get_market_indices(),
        "intervals": INTERVALS,
        "top10": top10,
        "top10_chart": top10_chart,
        "selected_symbol": selected_symbol,
        "selected_chart": selected_chart,
        "selected_interval": DEFAULT_INTERVAL,
        "selected_fundamentals": selected_fundamentals,
        "selected_financials_chart": selected_financials_chart,
        "group_summaries": group_summaries,
        "og_title": T["home_h1"],
        "og_description": T["home_meta_description"],
    })


def ticker_detail(request, symbol):
    lang = _get_lang(request)
    T = get_translations(lang)
    symbol = symbol.upper()
    interval = request.GET.get("interval", DEFAULT_INTERVAL)
    if interval not in INTERVALS:
        interval = DEFAULT_INTERVAL

    latest_result = (
        ScanResult.objects.select_related("ticker")
        .filter(ticker__symbol=symbol)
        .order_by("-date")
        .first()
    )
    fundamentals = get_fundamentals(symbol, lang)

    # Auditoría AdSense (27 ago 2026): esta vista no validaba el símbolo
    # y siempre devolvía 200, así que cualquier texto en la URL
    # (/accion/APPL/, /accion/ALPHABE/...) generaba una ficha completa
    # con todo en "N/D" — páginas vacías pero indexables, causa raíz
    # probable del flag "Contenido de bajo valor". Sin ScanResult NI
    # datos reales de Yahoo, no hay nada que mostrar: 404 real.
    if not latest_result and not fundamentals.get("has_data"):
        raise Http404(f"No hay datos para el símbolo '{symbol}'.")

    chart = build_price_chart(symbol, interval, lang)
    financials_chart = build_financials_chart(symbol, lang)
    commentary = build_ticker_commentary(latest_result, lang)

    # Título/meta por ticker: antes eran plantilla + símbolo únicamente
    # (72+ páginas casi idénticas entre sí para un rastreador). Con el
    # nombre real de la empresa y los datos del último scan, cada ficha
    # queda genuinamente distinta.
    company_name = fundamentals.get("company_name", symbol) if fundamentals else symbol
    page_title = T["ticker_page_title"].format(symbol=symbol, company=company_name)
    page_meta_description = T["ticker_page_description_base"].format(symbol=symbol, company=company_name)
    if latest_result:
        page_meta_description += T["ticker_page_description_data"].format(
            price=latest_result.price, rsi=latest_result.rsi, score=latest_result.score,
        )

    return render(request, "scanner/ticker_detail.html", {
        "symbol": symbol,
        "chart": chart,
        "interval": interval,
        "intervals": INTERVALS,
        "latest_result": latest_result,
        "fundamentals": fundamentals,
        "financials_chart": financials_chart,
        "commentary": commentary,
        "company_name": company_name,
        "page_title": page_title,
        "page_meta_description": page_meta_description,
        "og_title": page_title,
        "og_description": page_meta_description,
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
    financials_chart = build_financials_chart(symbol, lang)
    return render(request, "scanner/partials/indicators_panel.html", {
        "symbol": symbol,
        "fundamentals": fundamentals,
        "financials_chart": financials_chart,
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


