"""
Comentarios de interpretación automática para DSprofeta: RSI, MACD y
próximos eventos del calendario económico. Son reglas simples y
deterministas (umbrales fijos) — dan contexto rápido de lectura técnica,
no son asesoría financiera ni una señal de trading. Todo el texto sale
de config/translations.py (mismo mecanismo T/lang que usa el resto del
sitio) para poder traducirse con el selector ES/EN.
"""
from datetime import timedelta

from django.utils import timezone as dj_timezone

from config.translations import get_translations

from .models import EconomicEvent

RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Umbral relativo al precio del activo (no absoluto) para decidir si el
# MACD está "pegado a la señal" (sin dirección clara) o ya despegó —
# así funciona igual de bien en EUR/USD (~1.15) que en NASDAQ (~30,000).
MACD_NEUTRAL_THRESHOLD_PCT = 0.0003

IMPACT_CSS_LEVEL = {"high": "bad", "medium": "warning", "low": "good"}


def interpret_rsi(rsi_value, lang="es"):
    T = get_translations(lang)
    if rsi_value is None:
        return {"level": "unknown", "css_level": "unknown", "text": T["dsp_rsi_no_data"]}
    if rsi_value <= RSI_OVERSOLD:
        return {"level": "bullish", "css_level": "good", "text": T["dsp_rsi_oversold"].format(value=f"{rsi_value:.1f}")}
    if rsi_value >= RSI_OVERBOUGHT:
        return {"level": "bearish", "css_level": "bad", "text": T["dsp_rsi_overbought"].format(value=f"{rsi_value:.1f}")}
    return {"level": "neutral", "css_level": "warning", "text": T["dsp_rsi_neutral"].format(value=f"{rsi_value:.1f}")}


def interpret_macd(macd_line, macd_signal, reference_price, lang="es"):
    T = get_translations(lang)
    if macd_line is None or macd_signal is None:
        return {"level": "unknown", "css_level": "unknown", "text": T["dsp_macd_no_data"]}

    histogram = macd_line - macd_signal
    threshold = abs(reference_price) * MACD_NEUTRAL_THRESHOLD_PCT if reference_price else 0

    if histogram > threshold:
        return {"level": "bullish", "css_level": "good", "text": T["dsp_macd_bullish"]}
    if histogram < -threshold:
        return {"level": "bearish", "css_level": "bad", "text": T["dsp_macd_bearish"]}
    return {"level": "neutral", "css_level": "warning", "text": T["dsp_macd_neutral"]}


def upcoming_economic_events(hours_ahead=24, lang="es"):
    T = get_translations(lang)
    impact_comments = {"high": T["dsp_impact_high"], "medium": T["dsp_impact_medium"], "low": T["dsp_impact_low"]}

    now = dj_timezone.now()
    events = EconomicEvent.objects.filter(
        event_time__gte=now, event_time__lte=now + timedelta(hours=hours_ahead),
    ).order_by("event_time")

    return [
        {
            "event_time": e.event_time,
            "title": e.title,
            "country": e.country,
            "impact": e.impact,
            "css_level": IMPACT_CSS_LEVEL.get(e.impact, "unknown"),
            "comment": impact_comments.get(e.impact, ""),
        }
        for e in events
    ]
