"""
scanner/fundamentals.py

Datos fundamentales y de analistas por ticker, vía yfinance
(Ticker.info): recomendación de consenso, precio objetivo, market cap,
PER, PEG, endeudamiento, márgenes, dividendo y beta.

Nota sobre unidades (yfinance 1.5.x): `dividendYield` ya viene como
número de porcentaje (2.44 = 2.44%), mientras que `profitMargins` y
`returnOnEquity` vienen como fracción (0.28 = 28%). Si en el futuro
actualizas yfinance y estos números se ven raros, es lo primero a
revisar.
"""
import yfinance as yf
from django.core.cache import cache

FUNDAMENTALS_TTL = 3600

RECOMMENDATION_LABELS = {
    "es": {
        "strong_buy": "Compra fuerte",
        "strongbuy": "Compra fuerte",
        "buy": "Compra",
        "hold": "Mantener",
        "underperform": "Bajo rendimiento",
        "sell": "Venta",
        "none": "Sin datos",
    },
    "en": {
        "strong_buy": "Strong buy",
        "strongbuy": "Strong buy",
        "buy": "Buy",
        "hold": "Hold",
        "underperform": "Underperform",
        "sell": "Sell",
        "none": "No data",
    },
}
RECOMMENDATION_TONE = {
    "strong_buy": "positive",
    "strongbuy": "positive",
    "buy": "positive",
    "hold": "neutral",
    "underperform": "negative",
    "sell": "negative",
}

# yfinance siempre devuelve sector/industria y el resumen del negocio en
# inglés (vienen tal cual de Yahoo Finance, no hay versión en español).
# Traducimos los ~11 sectores GICS, que son un conjunto acotado y fijo;
# la industria (cientos de valores posibles) se deja en inglés.
SECTOR_LABELS = {
    "es": {
        "Technology": "Tecnología",
        "Healthcare": "Salud",
        "Financial Services": "Servicios financieros",
        "Consumer Cyclical": "Consumo cíclico",
        "Consumer Defensive": "Consumo defensivo",
        "Industrials": "Industrial",
        "Energy": "Energía",
        "Utilities": "Servicios públicos",
        "Real Estate": "Bienes raíces",
        "Basic Materials": "Materiales básicos",
        "Communication Services": "Servicios de comunicación",
    },
    "en": {},
}
BUSINESS_SUMMARY_MAX_LEN = 320


def get_fundamentals(symbol: str, lang: str = "es", include_summary: bool = True) -> dict:
    """
    include_summary=False evita traducir la descripción del negocio
    (llamada a Google Translate) cuando no hace falta — por ejemplo en
    save_scan_results(), que solo necesita los números fundamentales
    para cada uno de los ~60 tickers del scan diario y no debería
    quedar a merced de la latencia/límites de un traductor externo.
    """
    lang = lang if lang in RECOMMENDATION_LABELS else "es"
    cache_key = f"scanner:fundamentals:{symbol}:{lang}:{'full' if include_summary else 'nosummary'}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    ticker_obj = yf.Ticker(symbol)
    try:
        info = ticker_obj.info or {}
    except Exception:
        info = {}

    recommendation_key = (info.get("recommendationKey") or "").lower()
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
    target_mean = info.get("targetMeanPrice")

    sector_raw = info.get("sector") or ""

    result = {
        "has_data": bool(info),
        "current_price": current_price,
        "exchange": info.get("fullExchangeName") or info.get("exchange") or "",
        "company_name": info.get("longName") or info.get("shortName") or symbol,
        "sector": SECTOR_LABELS.get(lang, {}).get(sector_raw, sector_raw),
        "industry": info.get("industry") or "",
        "business_summary": (
            _truncate_summary(_localize_summary(info.get("longBusinessSummary") or "", lang))
            if include_summary else ""
        ),
        "recommendation_key": recommendation_key or None,
        "recommendation_label": RECOMMENDATION_LABELS[lang].get(recommendation_key, RECOMMENDATION_LABELS[lang]["none"]),
        "recommendation_tone": RECOMMENDATION_TONE.get(recommendation_key, "unknown"),
        "recommendation_mean": _round(info.get("recommendationMean")),
        "num_analysts": info.get("numberOfAnalystOpinions"),
        "target_mean_price": _round(target_mean),
        "target_high_price": _round(info.get("targetHighPrice")),
        "target_low_price": _round(info.get("targetLowPrice")),
        "target_upside_pct": (
            round((target_mean / current_price - 1) * 100, 1)
            if target_mean and current_price
            else None
        ),
        "market_cap": info.get("marketCap"),
        "market_cap_display": _format_market_cap(info.get("marketCap")),
        "trailing_pe": _round(info.get("trailingPE")),
        "forward_pe": _round(info.get("forwardPE")),
        "peg_ratio": _round(info.get("pegRatio") or info.get("trailingPegRatio")),
        "debt_to_equity": _round(info.get("debtToEquity")),
        "profit_margin_pct": _round((info.get("profitMargins") or 0) * 100) if info.get("profitMargins") is not None else None,
        "dividend_yield_pct": _round(info.get("dividendYield")),
        "beta": _round(info.get("beta")),
    }
    result["interpretations"] = _interpret(result, lang)
    result["gauges"] = _build_gauges(result)
    result["analyst_breakdown"] = _get_recommendation_breakdown(ticker_obj)

    if result["has_data"]:
        cache.set(cache_key, result, FUNDAMENTALS_TTL)
    return result


def _get_recommendation_breakdown(ticker_obj) -> dict | None:
    """
    Cuántos analistas recomiendan compra/mantener/venta, agrupado desde
    Ticker.recommendations (strongBuy+buy, hold, sell+strongSell) para
    el mes más reciente disponible ("0m").
    """
    try:
        df = ticker_obj.recommendations
        if df is None or df.empty:
            return None
        rows = df[df["period"] == "0m"]
        row = rows.iloc[0] if not rows.empty else df.iloc[0]
    except Exception:
        return None

    buy = int(row.get("strongBuy", 0) or 0) + int(row.get("buy", 0) or 0)
    hold = int(row.get("hold", 0) or 0)
    sell = int(row.get("sell", 0) or 0) + int(row.get("strongSell", 0) or 0)
    total = buy + hold + sell
    if total == 0:
        return None

    buy_pct = buy / total * 100
    hold_pct = hold / total * 100
    sell_pct = sell / total * 100

    return {
        "buy": buy,
        "hold": hold,
        "sell": sell,
        "total": total,
        "buy_pct": round(buy_pct, 1),
        "hold_pct": round(hold_pct, 1),
        "sell_pct": round(sell_pct, 1),
        "buy_stop": round(buy_pct, 2),
        "hold_stop": round(buy_pct + hold_pct, 2),
    }


# Rango visible (min, max) y umbrales (bueno, moderado) de cada medidor.
# "lower_better": el valor ideal es bajo (verde a la izquierda, rojo a la derecha).
# "higher_better": el valor ideal es alto (rojo a la izquierda, verde a la derecha).
# Los umbrales son referencias generales de mercado, no valen igual para
# todos los sectores (una utility "cara" en P/E puede ser normal en tech).
GAUGE_SPECS = {
    "trailing_pe": {"min": 0, "max": 50, "bounds": (20, 35), "direction": "lower_better", "skip_nonpositive": True},
    "forward_pe": {"min": 0, "max": 50, "bounds": (20, 35), "direction": "lower_better", "skip_nonpositive": True},
    "peg_ratio": {"min": 0, "max": 4, "bounds": (1, 2), "direction": "lower_better", "skip_nonpositive": True},
    "debt_to_equity": {"min": 0, "max": 250, "bounds": (50, 150), "direction": "lower_better", "skip_nonpositive": False},
    "profit_margin_pct": {"min": -10, "max": 40, "bounds": (5, 20), "direction": "higher_better", "skip_nonpositive": False},
    "beta": {"min": 0, "max": 3, "bounds": (0.9, 1.5), "direction": "lower_better", "skip_nonpositive": False},
}


def _build_gauges(data: dict) -> dict:
    return {key: _build_gauge(spec, data.get(key)) for key, spec in GAUGE_SPECS.items()}


def _build_gauge(spec: dict, value) -> dict:
    vmin, vmax = spec["min"], spec["max"]
    low, high = spec["bounds"]
    span = vmax - vmin
    lower_better = spec["direction"] == "lower_better"

    zone_colors = ("good", "warning", "bad") if lower_better else ("bad", "warning", "good")
    zone_widths = (
        round((low - vmin) / span * 100, 1),
        round((high - low) / span * 100, 1),
        round((vmax - high) / span * 100, 1),
    )
    zones = list(zip(zone_colors, zone_widths))

    if value is None or (spec["skip_nonpositive"] and value <= 0):
        return {"level": "unknown", "position": None, "zones": zones}

    if lower_better:
        level = "good" if value <= low else "warning" if value <= high else "bad"
    else:
        level = "bad" if value <= low else "warning" if value <= high else "good"

    clamped = max(vmin, min(vmax, value))
    position = round((clamped - vmin) / span * 100, 1)

    return {"level": level, "position": position, "zones": zones}


def _interpret(data: dict, lang: str = "es") -> dict:
    """Lectura en lenguaje simple de cada indicador clave y cómo podría
    influir en el valor futuro de la acción."""
    if lang == "en":
        return _interpret_en(data)
    return _interpret_es(data)


def _interpret_es(data: dict) -> dict:
    texts = {}

    pe = data.get("trailing_pe")
    if pe is None:
        texts["trailing_pe"] = "Sin datos suficientes para calcularlo (empresa sin utilidades recientes o dato no disponible)."
    elif pe < 15:
        texts["trailing_pe"] = "Bajo: el mercado paga poco por cada dólar de utilidad. Puede ser una oportunidad de valor, o una señal de que el mercado espera poco crecimiento."
    elif pe <= 25:
        texts["trailing_pe"] = "En rango razonable frente al promedio histórico del mercado (~20)."
    else:
        texts["trailing_pe"] = "Alto: el mercado paga una prima, normalmente porque espera crecimiento fuerte. Si la empresa no lo entrega, el precio puede corregir con fuerza."

    peg = data.get("peg_ratio")
    if peg is None:
        texts["peg_ratio"] = "Sin datos suficientes (requiere estimados de crecimiento a futuro)."
    elif peg < 1:
        texts["peg_ratio"] = "Por debajo de 1: el precio podría estar barato en relación a cuánto se espera que crezcan sus utilidades."
    elif peg <= 2:
        texts["peg_ratio"] = "Entre 1 y 2: el precio está más o menos alineado con el crecimiento esperado."
    else:
        texts["peg_ratio"] = "Por encima de 2: incluso considerando el crecimiento esperado, el precio luce caro."

    dte = data.get("debt_to_equity")
    if dte is None:
        texts["debt_to_equity"] = "Sin datos suficientes."
    elif dte < 50:
        texts["debt_to_equity"] = "Bajo apalancamiento: balance conservador, menos riesgo si suben las tasas de interés."
    elif dte <= 150:
        texts["debt_to_equity"] = "Apalancamiento moderado, normal en muchas industrias."
    else:
        texts["debt_to_equity"] = "Alto apalancamiento: más riesgo si sube el costo de la deuda o cae el flujo de caja."

    margin = data.get("profit_margin_pct")
    if margin is None:
        texts["profit_margin_pct"] = "Sin datos suficientes."
    elif margin < 5:
        texts["profit_margin_pct"] = "Margen bajo: el negocio tiene poco colchón si suben los costos."
    elif margin <= 20:
        texts["profit_margin_pct"] = "Margen saludable para la mayoría de las industrias."
    else:
        texts["profit_margin_pct"] = "Margen alto: suele indicar una ventaja competitiva fuerte (marca, escala, tecnología)."

    dividend = data.get("dividend_yield_pct")
    if not dividend:
        texts["dividend_yield_pct"] = "No reparte dividendos: reinvierte las utilidades en crecimiento en vez de repartirlas."
    else:
        texts["dividend_yield_pct"] = "Reparte una parte de sus utilidades como efectivo al accionista de forma recurrente."

    beta = data.get("beta")
    if beta is None:
        texts["beta"] = "Sin datos suficientes."
    elif beta < 0.9:
        texts["beta"] = "Menos volátil que el mercado en general (S&P 500 = 1.0)."
    elif beta <= 1.2:
        texts["beta"] = "Se mueve de forma similar al mercado en general."
    else:
        texts["beta"] = "Más volátil que el mercado: mayor potencial de ganancia, pero también de pérdida."

    return texts


def _interpret_en(data: dict) -> dict:
    texts = {}

    pe = data.get("trailing_pe")
    if pe is None:
        texts["trailing_pe"] = "Not enough data to calculate it (no recent earnings or data unavailable)."
    elif pe < 15:
        texts["trailing_pe"] = "Low: the market pays little for each dollar of earnings. Could be a value opportunity, or a sign the market expects little growth."
    elif pe <= 25:
        texts["trailing_pe"] = "In a reasonable range compared to the market's historical average (~20)."
    else:
        texts["trailing_pe"] = "High: the market is paying a premium, usually because it expects strong growth. If the company doesn't deliver, the price could correct sharply."

    peg = data.get("peg_ratio")
    if peg is None:
        texts["peg_ratio"] = "Not enough data (requires future growth estimates)."
    elif peg < 1:
        texts["peg_ratio"] = "Below 1: the price could be cheap relative to how much its earnings are expected to grow."
    elif peg <= 2:
        texts["peg_ratio"] = "Between 1 and 2: the price is roughly aligned with expected growth."
    else:
        texts["peg_ratio"] = "Above 2: even accounting for expected growth, the price looks expensive."

    dte = data.get("debt_to_equity")
    if dte is None:
        texts["debt_to_equity"] = "Not enough data."
    elif dte < 50:
        texts["debt_to_equity"] = "Low leverage: conservative balance sheet, less risk if interest rates rise."
    elif dte <= 150:
        texts["debt_to_equity"] = "Moderate leverage, normal in many industries."
    else:
        texts["debt_to_equity"] = "High leverage: more risk if the cost of debt rises or cash flow drops."

    margin = data.get("profit_margin_pct")
    if margin is None:
        texts["profit_margin_pct"] = "Not enough data."
    elif margin < 5:
        texts["profit_margin_pct"] = "Low margin: the business has little cushion if costs rise."
    elif margin <= 20:
        texts["profit_margin_pct"] = "Healthy margin for most industries."
    else:
        texts["profit_margin_pct"] = "High margin: usually indicates a strong competitive advantage (brand, scale, technology)."

    dividend = data.get("dividend_yield_pct")
    if not dividend:
        texts["dividend_yield_pct"] = "Doesn't pay dividends: reinvests earnings into growth instead of distributing them."
    else:
        texts["dividend_yield_pct"] = "Pays out a portion of its earnings as cash to shareholders on a recurring basis."

    beta = data.get("beta")
    if beta is None:
        texts["beta"] = "Not enough data."
    elif beta < 0.9:
        texts["beta"] = "Less volatile than the overall market (S&P 500 = 1.0)."
    elif beta <= 1.2:
        texts["beta"] = "Moves similarly to the overall market."
    else:
        texts["beta"] = "More volatile than the market: higher potential gain, but also higher potential loss."

    return texts


def _localize_summary(text: str, lang: str) -> str:
    """
    yfinance solo trae el resumen del negocio (longBusinessSummary) en
    inglés — no hay versión en español desde la fuente. Para lang="es"
    lo traducimos con Google Translate (vía deep-translator, sin API
    key). Si la traducción falla por cualquier motivo (sin internet,
    servicio caído, texto vacío), se devuelve el original en inglés en
    vez de romper la página — mejor mostrar la versión en inglés que
    nada.
    """
    text = (text or "").strip()
    if not text or lang != "es":
        return text

    try:
        from deep_translator import GoogleTranslator

        # GoogleTranslator (gratuito) tiene un límite de ~5000
        # caracteres por llamada; longBusinessSummary nunca se acerca
        # a eso, pero se recorta por seguridad antes de traducir.
        translated = GoogleTranslator(source="en", target="es").translate(text[:4500])
        return translated or text
    except Exception as exc:
        import logging
        logging.getLogger("scanner").exception("Fallo al traducir business_summary: %s", exc)
        return text


def _truncate_summary(text: str, max_len: int = BUSINESS_SUMMARY_MAX_LEN) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return truncated + "…"


def _round(value, digits: int = 2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _format_market_cap(value) -> str:
    if not value:
        return "N/D"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    if value >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.0f}"
