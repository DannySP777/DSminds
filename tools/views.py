"""
tools/views.py

Portada "Trading Análisis" (análisis diario del NASDAQ, datos armados en
tools/analysis.py) y herramientas interactivas gratuitas (calculadoras)
— estas últimas 100% client-side: sus vistas solo renderizan la página,
toda la matemática vive en static/js/tools.js. No hay modelos ni persistencia: cada calculadora
recalcula en vivo con JS, no hace falta un roundtrip al servidor.
"""
import json

from django.shortcuts import render

from config.translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations

from .analysis import ASSETS, DEFAULT_SYMBOL, asset_tabs, build_analysis


def _get_lang(request):
    # ?lang= manda sobre la cookie — debe resolver igual que
    # config.context_processors._resolve_lang, o T/LANG del layout
    # queda desincronizado del idioma que arma esta vista.
    lang = request.GET.get("lang") or request.COOKIES.get("site_lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def trading_analysis(request):
    lang = _get_lang(request)
    T = get_translations(lang)
    symbol = request.GET.get("asset", DEFAULT_SYMBOL)
    if symbol not in ASSETS:
        symbol = DEFAULT_SYMBOL
    key = ASSETS[symbol]["key"]
    asset_name = T[f"ta_asset_{key}_name"]

    analysis = build_analysis(symbol, lang)
    page_title = T["ta_page_title"].format(asset=asset_name)
    meta_description = T["ta_meta_description"].format(asset=asset_name, aka=T[f"ta_asset_{key}_aka"])

    # Preguntas frecuentes: texto visible + FAQPage (JSON-LD) con las mismas respuestas.
    faq = analysis["faq"] if analysis else []
    faq_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
            for item in faq
        ],
    }, ensure_ascii=False).replace("</", "<\\/") if faq else ""

    return render(request, "tools/analysis.html", {
        "h1": T["ta_h1_asset"].format(asset=asset_name),
        "keywords": T["ta_keywords"].format(asset=asset_name, aka=T[f"ta_asset_{key}_aka"]),
        "h2_chart": T["ta_h2_chart"].format(asset=asset_name),
        "h2_macd": T["ta_h2_macd"].format(asset=asset_name),
        "h2_levels": T["ta_h2_levels"].format(asset=asset_name),
        "h2_forecast": T["ta_h2_forecast"].format(asset=asset_name),
        "h2_reading": T["ta_h2_reading"].format(asset=asset_name),
        "intro": T[f"ta_asset_{key}_intro"],
        "faq": faq,
        "faq_title": T["ta_faq_title"].format(asset=asset_name),
        "faq_jsonld": faq_jsonld,
        "date_modified": analysis["as_of"].strftime("%Y-%m-%d") if analysis else "",
        "ta": analysis,
        "chart_payload": analysis["chart_payload"] if analysis else None,
        "asset_tabs": asset_tabs(symbol, lang),
        "selected_symbol": symbol,
        "asset_name": asset_name,
        "kicker": T["ta_kicker"].format(asset=asset_name),
        "empty_text": T["ta_chart_empty"].format(asset=asset_name),
        "page_title": page_title,
        "page_meta_description": meta_description,
        "og_title": page_title,
        "og_description": meta_description,
    })


def tools_index(request):
    lang = _get_lang(request)
    T = get_translations(lang)
    return render(request, "tools/index.html", {
        "og_title": T["tools_index_h1"],
        "og_description": T["tools_index_meta_description"],
    })


def compound_interest(request):
    lang = _get_lang(request)
    T = get_translations(lang)
    return render(request, "tools/compound_interest.html", {
        "og_title": T["tool_compound_h1"],
        "og_description": T["tool_compound_meta_description"],
    })


def risk_reward(request):
    lang = _get_lang(request)
    T = get_translations(lang)
    return render(request, "tools/risk_reward.html", {
        "og_title": T["tool_risk_h1"],
        "og_description": T["tool_risk_meta_description"],
    })


def fair_value_gap(request):
    lang = _get_lang(request)
    T = get_translations(lang)
    return render(request, "tools/fair_value_gap.html", {
        "og_title": T["tool_fvg_h1"],
        "og_description": T["tool_fvg_meta_description"],
    })
