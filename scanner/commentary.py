"""
Comentario técnico/fundamental genuino por ticker, generado con reglas
fijas sobre los datos reales del último scan de esa acción — mismo
criterio que blog/services.py::_build_conclusion y
scanner/services.py::build_group_summary, aplicado ahora a la ficha
individual de cada acción.

Por qué existe: la auditoría de políticas de AdSense (27 ago 2026)
identificó que las fichas de acción compartían casi todo su texto
entre sí — metodología, leyenda de gráfica y definiciones de métricas
son idénticas palabra por palabra en todas, y lo único que cambiaba
eran los números y un resumen de negocio copiado de un tercero. Este
módulo agrega, por ticker, 3-4 oraciones que sí son genuinamente
distintas de una acción a otra porque interpretan SUS números
específicos, no solo los muestran.
"""
from config.translations import get_translations


def build_ticker_commentary(result, lang: str = "es") -> str:
    """
    `result` es un ScanResult (o cualquier objeto con los mismos
    atributos: price, rsi, macd_bullish, above_ma200, breakout,
    relative_volume, target_upside_pct, trailing_pe, peg_ratio, group,
    momentum_rank). Devuelve una cadena vacía si no hay suficientes
    datos para decir algo real (mejor no mostrar nada que mostrar una
    plantilla vacía).
    """
    if result is None:
        return ""

    T = get_translations(lang)
    parts = []

    rsi = float(result.rsi) if result.rsi is not None else None
    relvol = float(result.relative_volume) if result.relative_volume is not None else None

    # --- tendencia de fondo + RSI ---
    if rsi is not None:
        if result.above_ma200 and rsi < 50:
            parts.append(T["commentary_trend_up_rsi_room"].format(rsi=rsi))
        elif result.above_ma200 and rsi >= 70:
            parts.append(T["commentary_trend_up_rsi_hot"].format(rsi=rsi))
        elif result.above_ma200:
            parts.append(T["commentary_trend_up_rsi_neutral"].format(rsi=rsi))
        elif rsi <= 30:
            parts.append(T["commentary_trend_down_rsi_oversold"].format(rsi=rsi))
        else:
            parts.append(T["commentary_trend_down_rsi_neutral"].format(rsi=rsi))

    # --- MACD + ruptura de rango ---
    if result.macd_bullish and result.breakout:
        parts.append(T["commentary_macd_breakout_both"])
    elif result.macd_bullish:
        parts.append(T["commentary_macd_only"])
    elif result.breakout:
        parts.append(T["commentary_breakout_only"])
    else:
        parts.append(T["commentary_no_technical_signal"])

    # --- volumen relativo ---
    if relvol is not None:
        if relvol >= 2:
            parts.append(T["commentary_relvol_high"].format(relvol=round(relvol, 2)))
        elif relvol >= 1.3:
            parts.append(T["commentary_relvol_above"].format(relvol=round(relvol, 2)))
        elif relvol < 0.7:
            parts.append(T["commentary_relvol_low"].format(relvol=round(relvol, 2)))

    # --- upside al precio objetivo de analistas ---
    upside = result.target_upside_pct
    if upside is not None:
        if upside >= 25:
            parts.append(T["commentary_upside_strong"].format(upside=upside))
        elif upside >= 0:
            parts.append(T["commentary_upside_modest"].format(upside=upside))
        else:
            parts.append(T["commentary_upside_negative"].format(upside=upside))

    # --- valuación (PEG, si hay datos) ---
    if result.peg_ratio is not None:
        peg = float(result.peg_ratio)
        if peg < 1:
            parts.append(T["commentary_peg_cheap"].format(peg=peg))
        elif peg > 2.5:
            parts.append(T["commentary_peg_expensive"].format(peg=peg))

    # --- puesto en el sistema solar, si esta fila viene de esa pipeline ---
    if getattr(result, "group", "") and getattr(result, "momentum_rank", None):
        group_label = T.get(f"solar_group_{result.group}", result.group)
        parts.append(T["commentary_group_rank"].format(rank=result.momentum_rank, group=group_label))

    return " ".join(parts)
