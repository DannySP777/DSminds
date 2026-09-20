"""
tools/analysis.py

Datos de la pantalla "Trading Análisis": lectura de tendencia de un
activo a elegir (NASDAQ 100, Oro, EUR/USD o Bitcoin: alcista/bajista con
las señales que la sustentan), soportes y resistencias, pronóstico de
las próximas 5 velas y el calendario económico del mes con su
significado para ese activo.

No consulta ninguna API externa en cada visita: las velas salen de la
tabla PriceBar (llenada por el ciclo de sync de dsprofeta), el modelo de
predicción es el LightGBM diario ya entrenado (dsprofeta.ml) y el
calendario sale de news.EconomicEvent (llenado por fetch_calendar).
Reutiliza las funciones de dsprofeta en vez de duplicarlas: mismas
features, mismo modelo, mismo detector de niveles.
"""
import logging
from datetime import timedelta

import pandas as pd
from django.core.cache import cache
from django.utils import timezone
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import AverageTrueRange

from config.translations import get_translations
from dsprofeta.features import (
    FEATURE_COLUMNS, _add_technical_columns, _economic_event_features,
    _load_economic_events, _news_features, build_backtest_samples, price_bars_dataframe,
)
from dsprofeta.levels import detect_levels
from dsprofeta.ml import _load_active_run, _load_model
from dsprofeta.models import Asset, PriceBar
from news.models import EconomicEvent

from .calendar_meanings import explain_event

logger = logging.getLogger(__name__)

# Activos que se pueden elegir en la pantalla (en este orden). `key` es el
# sufijo de las traducciones ta_asset_<key>_*; `digits` son los decimales de
# cada activo: price = precio exacto (lectura OHLC, payload), level =
# soportes/resistencias y tablas, tick = eje de precio de la gráfica —
# EUR/USD cotiza ~1.15 y necesita 4-5 decimales, el NASDAQ ~29.600 no.
# `weekends` = el mercado opera sábado/domingo (cripto): sin eso el eje
# ocultaría esas velas y el pronóstico las saltaría. `level_bars` = velas
# que se miran para detectar niveles (~3 meses en cada mercado).
ASSETS = {
    "NDX100": {"key": "ndx", "digits": {"price": 2, "level": 0, "tick": 0}, "weekends": False, "level_bars": 60},
    "GOLD": {"key": "gold", "digits": {"price": 2, "level": 1, "tick": 0}, "weekends": False, "level_bars": 60},
    "EURUSD": {"key": "eurusd", "digits": {"price": 5, "level": 4, "tick": 3}, "weekends": False, "level_bars": 60},
    "BTCUSD": {"key": "btc", "digits": {"price": 2, "level": 0, "tick": 0}, "weekends": True, "level_bars": 90},
}
DEFAULT_SYMBOL = "NDX100"
CHART_BARS = 300  # velas que se mandan al navegador (cubre 1 año + calentamiento de la SMA 200 ya calculada)
FORECAST_STEPS = 5
LEVEL_PIVOT_WINDOW = 3
LEVEL_MAX = 4
FORECAST_CACHE_TTL = 60 * 60

def _long_date(value, lang):
    """"18 de septiembre de 2026" / "September 18, 2026" (value: date, datetime o "YYYY-MM-DD")."""
    if isinstance(value, str):
        value = pd.Timestamp(value)
    names = MONTH_NAMES["en" if lang == "en" else "es"]
    if lang == "en":
        return f"{names[value.month - 1]} {value.day}, {value.year}"
    return f"{value.day} de {names[value.month - 1]} de {value.year}"


MONTH_NAMES = {
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
           "septiembre", "octubre", "noviembre", "diciembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
}


def _iso(ts):
    return ts.strftime("%Y-%m-%d")


def _num(value, digits=2):
    return None if pd.isna(value) else round(float(value), digits)


def _indicator_frame(df):
    """Indicadores sobre TODO el historial (la SMA 200 necesita 200 velas
    de calentamiento); el recorte a CHART_BARS se hace después."""
    out = df.copy()
    close = out["close"]
    out["sma20"] = SMAIndicator(close, window=20).sma_indicator()
    out["sma50"] = SMAIndicator(close, window=50).sma_indicator()
    out["sma200"] = SMAIndicator(close, window=200).sma_indicator()
    out["rsi"] = RSIIndicator(close, window=14).rsi()
    macd_calc = MACD(close)
    out["macd"] = macd_calc.macd()
    out["macd_signal"] = macd_calc.macd_signal()
    out["atr"] = AverageTrueRange(out["high"], out["low"], close, window=14).average_true_range()
    return out


# --------------------------------------------------------------------- forecast

def _forecast_bars(asset, df, cfg, steps=FORECAST_STEPS):
    """
    Proyecta las próximas `steps` velas diarias con el MISMO modelo
    LightGBM diario de dsprofeta (predice el % de cambio al próximo
    cierre). Un modelo de "1 paso" se vuelve multi-paso de forma
    recursiva: cada cierre proyectado se agrega como una vela más, se
    recalculan los indicadores y se predice la siguiente. El error se
    acumula paso a paso, por eso la banda de incertidumbre se ensancha
    con la raíz del número de velas.
    Devuelve [] si todavía no hay un modelo diario entrenado.
    """
    digits = cfg["digits"]["price"]
    try:
        run = _load_active_run(asset, PriceBar.Timeframe.D1)
    except ValueError:
        return [], None

    cache_key = f"ta_forecast:{asset.symbol}:{_iso(df.index[-1])}:{run.version}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached, run

    model = _load_model(run)
    work = df[["open", "high", "low", "close", "volume"]].copy()
    last_time = work.index[-1]
    events = _load_economic_events(last_time - timedelta(hours=24), last_time + timedelta(days=steps + 2))
    avg_volume = float(work["volume"].tail(20).mean())
    # MAE del holdout -> desvío típico aproximado (MAE ~ 0.8 sigma en una normal).
    sigma_1 = float(run.mae) * 1.25

    start_day = last_time + pd.Timedelta(days=1)
    future_days = (
        pd.date_range(start_day, periods=steps) if cfg["weekends"] else pd.bdate_range(start_day, periods=steps)
    )
    bars = []
    for step, day in enumerate(future_days, start=1):
        feats = _add_technical_columns(work.copy(), 100)
        row = feats.iloc[-1][["close", "rsi", "macd_line", "macd_signal", "atr", "sma_20",
                              "fib_position_pct", "fib_distance_pct"]].to_dict()
        row.update(_economic_event_features(work.index[-1], events))
        row.update(_news_features(work.index[-1], []))
        if any(pd.isna(v) for v in row.values()):
            break

        predicted_return = float(model.predict(pd.DataFrame([row], columns=FEATURE_COLUMNS))[0])
        prev_close = float(work["close"].iloc[-1])
        close = prev_close * (1 + predicted_return)
        atr = float(feats["atr"].iloc[-1])
        # Vela proyectada: el cuerpo va del cierre anterior al cierre
        # proyectado; las mechas usan un cuarto del ATR (rango típico
        # diario) para que se lea como vela y no como una línea.
        high = max(prev_close, close) + 0.25 * atr
        low = min(prev_close, close) - 0.25 * atr
        spread = sigma_1 * (step ** 0.5)
        bars.append({
            "x": _iso(day), "o": round(prev_close, digits), "h": round(high, digits), "l": round(low, digits),
            "c": round(close, digits), "band_hi": round(close + spread, digits), "band_lo": round(close - spread, digits),
            "change_pct": round(predicted_return * 100, 3),
        })
        work.loc[day] = [prev_close, high, low, close, avg_volume]

    cache.set(cache_key, bars, FORECAST_CACHE_TTL)
    return bars, run


def _holdout_direction_accuracy(asset, run):
    """
    Qué tan seguido el modelo diario acertó la DIRECCIÓN (sube/baja) de la
    vela siguiente en las sesiones que no vio al entrenar: la parte de
    test del split temporal (20 % final) más lo que llegó después. No se
    usan las predicciones ya resueltas en vivo, que son muy pocas
    (decenas) para ser una estadística confiable. Se devuelve el número tal cual, incluso si es
    modesto: mostrarlo es parte de no vender el pronóstico como certeza.
    """
    cache_key = f"ta_direction:{asset.symbol}:{run.version}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached or None

    holdout = max(30, run.n_samples - int(run.n_samples * 0.8))
    samples = build_backtest_samples(asset, PriceBar.Timeframe.D1, n_points=holdout)
    if len(samples) < 30:
        cache.set(cache_key, False, FORECAST_CACHE_TTL * 6)
        return None

    model = _load_model(run)
    features = pd.DataFrame([s["features"] for s in samples], columns=FEATURE_COLUMNS)
    predicted_returns = model.predict(features)
    hits = total = 0
    for sample, predicted_return in zip(samples, predicted_returns):
        actual_move = sample["actual_close"] - sample["base_close"]
        if predicted_return == 0 or actual_move == 0:
            continue
        total += 1
        hits += (predicted_return > 0) == (actual_move > 0)
    result = {"accuracy": round(float(hits) / total * 100, 1), "n": total} if total else None
    cache.set(cache_key, result if result else False, FORECAST_CACHE_TTL * 6)
    return result


# ------------------------------------------------------------------ MACD por hora

MACD_HOURLY_BARS = 150        # velas de 1 hora que se dibujan
MACD_HOURLY_FETCH = 450       # historial leído para que el MACD (26+9) ya esté "caliente"


def _hourly_macd(asset, digits, T):
    """
    MACD(12,26,9) sobre velas de 1 HORA (PriceBar 1h, ya sincronizadas por el
    ciclo horario de dsprofeta): líneas MACD y señal + histograma de las
    últimas MACD_HOURLY_BARS horas, y una lectura en palabras del estado
    actual (¿MACD sobre su señal?, ¿el impulso se fortalece o se debilita?,
    ¿hubo cruce reciente?). Devuelve None si aún no hay suficientes velas.
    """
    bars = list(
        PriceBar.objects.filter(asset=asset, timeframe=PriceBar.Timeframe.H1)
        .order_by("-timestamp")[:MACD_HOURLY_FETCH]
    )
    if len(bars) < 80:
        return None
    bars.reverse()
    close = pd.Series([float(b.close) for b in bars], index=[b.timestamp for b in bars])
    calc = MACD(close)
    frame = pd.DataFrame({"macd": calc.macd(), "signal": calc.macd_signal(), "hist": calc.macd_diff()}).dropna()
    frame = frame.tail(MACD_HOURLY_BARS)
    if len(frame) < 30:
        return None

    dp = digits["price"] + 1 if digits["price"] > 2 else 3
    last, prev = frame.iloc[-1], frame.iloc[-2]
    bullish = bool(last["macd"] > last["signal"])
    strengthening = abs(last["hist"]) > abs(prev["hist"])
    signs = (frame["hist"].tail(6) > 0).tolist()
    crossed = any(signs[i] != signs[i + 1] for i in range(len(signs) - 1))

    text = T["ta_macdh_state_up" if bullish else "ta_macdh_state_down"] + " " + T[
        "ta_macdh_strengthening" if strengthening else "ta_macdh_weakening"
    ]
    if crossed:
        text += " " + T["ta_macdh_cross"]
    return {
        "available": True,
        "bullish": bullish,
        "state_text": text,
        "payload": {
            "x": [ts.strftime("%Y-%m-%dT%H:%M:%SZ") for ts in frame.index],
            "macd": [round(float(v), dp) for v in frame["macd"]],
            "signal": [round(float(v), dp) for v in frame["signal"]],
            "hist": [round(float(v), dp) for v in frame["hist"]],
            "digits": dp,
        },
    }


# ------------------------------------------------------------- lectura semanal

WEEKLY_MIN_BARS = 60


def _weekly_read(asset):
    """
    Tendencia en velas SEMANALES con cinco comprobaciones (precio vs. medias
    de 10 y 40 semanas ~ 50 y 200 días, cruce de ambas, RSI(14) y MACD
    semanales): mayoría = alcista/bajista. Es el complemento de largo plazo
    de la lectura diaria — a veces difieren, y eso también informa.
    Devuelve None si aún no hay suficientes velas semanales.
    """
    df = price_bars_dataframe(asset, PriceBar.Timeframe.W1)
    if len(df) < WEEKLY_MIN_BARS:
        return None
    close = df["close"]
    sma10 = SMAIndicator(close, window=10).sma_indicator().iloc[-1]
    sma40 = SMAIndicator(close, window=40).sma_indicator().iloc[-1]
    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
    macd_calc = MACD(close)
    macd_line, macd_signal = macd_calc.macd().iloc[-1], macd_calc.macd_signal().iloc[-1]
    if any(pd.isna(v) for v in (sma10, sma40, rsi, macd_line, macd_signal)):
        return None
    last = float(close.iloc[-1])
    votes = [last > sma10, last > sma40, sma10 > sma40, rsi >= 50, macd_line > macd_signal]
    bulls = sum(bool(v) for v in votes)
    bullish = bulls > len(votes) / 2
    return {"bullish": bullish, "agree": bulls if bullish else len(votes) - bulls, "total": len(votes)}


# ------------------------------------------------------------------ trend view

def _swing_structure(df, window=10):
    """Máximos/mínimos crecientes (alcista) o decrecientes (bajista) al
    comparar las últimas `window` velas con las `window` anteriores."""
    recent, prior = df.tail(window), df.iloc[-2 * window:-window]
    higher_high = recent["high"].max() > prior["high"].max()
    higher_low = recent["low"].min() > prior["low"].min()
    if higher_high and higher_low:
        return 1
    if not higher_high and not higher_low:
        return -1
    return 1 if df["close"].iloc[-1] >= df["close"].iloc[-1 - window] else -1


def _build_signals(df, forecast, T, d):
    last = df.iloc[-1]
    close = float(last["close"])
    signals = []

    def add(key, bullish, value):
        signals.append({
            "key": key,
            "label": T[f"ta_sig_{key}"],
            "bullish": bool(bullish),
            "value": value,
            "why": T[f"ta_sig_{key}_up"] if bullish else T[f"ta_sig_{key}_down"],
        })

    add("sma50", close > last["sma50"], f"{close:,.{d}f} vs {last['sma50']:,.{d}f}")
    add("sma200", close > last["sma200"], f"{close:,.{d}f} vs {last['sma200']:,.{d}f}")
    add("cross", last["sma50"] > last["sma200"], f"{last['sma50']:,.{d}f} / {last['sma200']:,.{d}f}")
    add("slope", last["sma20"] > df["sma20"].iloc[-6], f"{(last['sma20'] / df['sma20'].iloc[-6] - 1) * 100:+.2f}%")
    add("rsi", last["rsi"] >= 50, f"{last['rsi']:.0f}")
    add("macd", last["macd"] > last["macd_signal"], f"{last['macd']:.4g} / {last['macd_signal']:.4g}")
    add("structure", _swing_structure(df) > 0, "")
    if forecast:
        add("forecast", forecast[-1]["c"] > close, f"{(forecast[-1]['c'] / close - 1) * 100:+.2f}%")
    return signals


def _verdict(signals, df):
    bulls = sum(1 for s in signals if s["bullish"])
    total = len(signals)
    if bulls * 2 == total:
        # Empate exacto: desempata la tendencia de mediano plazo (precio vs SMA 50).
        bullish = df["close"].iloc[-1] > df["sma50"].iloc[-1]
    else:
        bullish = bulls * 2 > total
    agree = bulls if bullish else total - bulls
    ratio = agree / total
    strength = "strong" if ratio >= 0.75 else "moderate" if ratio >= 0.6 else "weak"
    return {"bullish": bullish, "agree": agree, "total": total, "ratio": round(ratio, 3), "strength": strength}


def _narrative(verdict, levels, last_close, forecast, lang, the, d, weekly=None):
    """Lectura del día en prosa (ramas explícitas por idioma, porque la frase cambia de estructura)."""
    support = levels["supports"][0] if levels["supports"] else None
    resistance = levels["resistances"][0] if levels["resistances"] else None
    end = forecast[-1] if forecast else None
    parts = []

    if lang == "en":
        direction = "bullish" if verdict["bullish"] else "bearish"
        parts.append(
            f"{verdict['agree']} of {verdict['total']} signals point {direction}, so {the} "
            f"reads as {direction} ({verdict['strength']} conviction)."
        )
        if end:
            move = (end["c"] / last_close - 1) * 100
            parts.append(
                f"The model projects a close near {end['c']:,.{d}f} in {len(forecast)} sessions ({move:+.1f}%), "
                f"with a likely range of {end['band_lo']:,.{d}f}–{end['band_hi']:,.{d}f}."
            )
            if (move > 0) != verdict["bullish"]:
                parts.append("Note that the model points against the trend: a reason for caution, not a reversal signal.")
        if weekly:
            word = "bullish" if weekly["bullish"] else "bearish"
            parts.append(f"On weekly candles the read is {word} ({weekly['agree']} of {weekly['total']} signals)"
                         + (", matching the daily read." if weekly["bullish"] == verdict["bullish"]
                            else ", which differs from the daily read: it is worth watching both timeframes."))
        if verdict["bullish"]:
            if support:
                parts.append(f"A pullback toward the {support['price']:,.{d}f} support (tested {support['touches']}x) is the classic area where buyers step back in.")
            if resistance:
                parts.append(f"Watch {resistance['price']:,.{d}f}: a daily close above it would confirm the move; if price is rejected there, sellers have defended that area before.")
        else:
            if resistance:
                parts.append(f"A bounce toward the {resistance['price']:,.{d}f} resistance (tested {resistance['touches']}x) is where sellers have defended before.")
            if support:
                parts.append(f"Watch {support['price']:,.{d}f}: a daily close below it would confirm more downside; holding it points to a relief bounce.")
        return " ".join(parts)

    direction = "alcista" if verdict["bullish"] else "bajista"
    pointing = "al alza" if verdict["bullish"] else "a la baja"
    strength = {"strong": "fuerte", "moderate": "moderada", "weak": "débil"}[verdict["strength"]]
    parts.append(
        f"{verdict['agree']} de {verdict['total']} señales apuntan {pointing}, así que {the} "
        f"se lee {direction} (convicción {strength})."
    )
    if end:
        move = (end["c"] / last_close - 1) * 100
        parts.append(
            f"El modelo proyecta un cierre cerca de {end['c']:,.{d}f} en {len(forecast)} sesiones ({move:+.1f} %), "
            f"con un rango probable de {end['band_lo']:,.{d}f}–{end['band_hi']:,.{d}f}."
        )
        if (move > 0) != verdict["bullish"]:
            parts.append("Ojo: el modelo apunta contra la tendencia; es una razón para ir con cautela, no una señal de reversión.")
    if weekly:
        word = "alcista" if weekly["bullish"] else "bajista"
        parts.append(f"En velas semanales la lectura es {word} ({weekly['agree']} de {weekly['total']} señales)"
                     + (", en línea con la lectura diaria." if weekly["bullish"] == verdict["bullish"]
                        else ", distinta de la lectura diaria: conviene vigilar ambos plazos."))
    if verdict["bullish"]:
        if support:
            parts.append(f"Un retroceso hacia el soporte de {support['price']:,.{d}f} (probado {support['touches']} {'vez' if support['touches'] == 1 else 'veces'}) es la zona clásica donde los compradores suelen volver.")
        if resistance:
            parts.append(f"Vigila {resistance['price']:,.{d}f}: un cierre diario por encima confirmaría el movimiento; si el precio es rechazado ahí, los vendedores ya defendieron esa zona antes.")
    else:
        if resistance:
            parts.append(f"Un rebote hacia la resistencia de {resistance['price']:,.{d}f} (probada {resistance['touches']} {'vez' if resistance['touches'] == 1 else 'veces'}) es donde los vendedores ya se defendieron antes.")
        if support:
            parts.append(f"Vigila {support['price']:,.{d}f}: un cierre diario por debajo confirmaría más caída; si lo sostiene, apunta a un rebote técnico.")
    return " ".join(parts)


# -------------------------------------------------------------------- calendar

def _month_bounds(now):
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (start + timedelta(days=32)).replace(day=1)
    return start, next_month


def _range_label(first, last, lang):
    """"14–20 sep" (o "28 sep – 4 oct" si cruza de mes)."""
    names = MONTH_NAMES["en" if lang == "en" else "es"]
    m1, m2 = names[first.month - 1][:3], names[last.month - 1][:3]
    if first.month == last.month:
        return f"{first.day}–{last.day} {m2}"
    return f"{first.day} {m1} – {last.day} {m2}"


def build_month_calendar(lang="es", asset_key="ndx", now=None):
    """Eventos (USD, impacto medio/alto) del mes en curso con su
    significado, más lo que caiga en la semana actual y la siguiente (aunque
    crucen de mes). El feed gratuito solo entrega la semana actual y, cuando
    ya la publicó, la siguiente; fetch_calendar conserva 45 días, así que el
    mes se completa a medida que pasan las semanas."""
    now = now or timezone.now()
    month_start, month_end = _month_bounds(now)

    today = now.date()
    this_monday = today - timedelta(days=today.weekday())
    next_monday = this_monday + timedelta(days=7)
    after_next = next_monday + timedelta(days=7)

    def midnight(day):
        return now.replace(year=day.year, month=day.month, day=day.day, hour=0, minute=0, second=0, microsecond=0)

    window_start = min(month_start, midnight(this_monday))
    window_end = max(month_end, midnight(after_next))
    events = EconomicEvent.objects.filter(event_time__gte=window_start, event_time__lt=window_end).order_by("event_time")

    rows = []
    for e in events:
        meaning = explain_event(e.title, e.impact, lang, asset_key)
        day = e.event_time.date()
        if day < today:
            when = "past"
        elif day == today:
            when = "today"
        else:
            when = "upcoming"
        if this_monday <= day < next_monday:
            week = "this"
        elif next_monday <= day < after_next:
            week = "next"
        else:
            week = "other"
        rows.append({
            "id": e.pk,
            "time": e.event_time,
            "iso": e.event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "title": e.title,
            "name": meaning["name"] or e.title,
            "what": meaning["what"],
            "effect": meaning["effect"],
            "impact": e.impact,
            "stars": e.stars,
            "forecast": e.forecast, "previous": e.previous, "actual": e.actual,
            "when": when,
            "week": week,
            "in_month": month_start <= e.event_time < month_end,
        })

    month_rows = [r for r in rows if r["in_month"]]
    upcoming_high = next((r for r in rows if r["impact"] == "high" and r["time"] >= now), None)
    return {
        "rows": rows,
        "month_start": month_start,
        "month_label": f"{MONTH_NAMES['en' if lang == 'en' else 'es'][month_start.month - 1]} {month_start.year}",
        "high_count": sum(1 for r in month_rows if r["impact"] == "high"),
        "month_count": len(month_rows),
        "counts": {
            "month": len(month_rows),
            "this": sum(1 for r in rows if r["week"] == "this"),
            "next": sum(1 for r in rows if r["week"] == "next"),
        },
        "ranges": {
            "month": f"{MONTH_NAMES['en' if lang == 'en' else 'es'][month_start.month - 1]} {month_start.year}",
            "this": _range_label(this_monday, this_monday + timedelta(days=6), lang),
            "next": _range_label(next_monday, next_monday + timedelta(days=6), lang),
        },
        "upcoming_high": upcoming_high,
        "upcoming_high_days": (upcoming_high["time"].date() - today).days if upcoming_high else None,
    }


def _build_faq(T, lang, key, verdict, as_of, supports, resistances, forecast, digits, last_close, weekly=None):
    """Preguntas frecuentes con respuestas armadas con los datos reales del día
    (veredicto, niveles, pronóstico). Se muestran en la página y se publican
    como FAQPage (JSON-LD): el texto visible y el estructurado son el mismo."""
    d = digits["level"]
    the = T[f"ta_asset_{key}_the"]
    cap = the[:1].upper() + the[1:]
    faq = [
        {
            "q": T["ta_faq_q_trend"].format(the=cap),
            "a": T["ta_faq_a_trend"].format(
                date=_long_date(as_of, lang), agree=verdict["agree"], total=verdict["total"],
                pointing=T["ta_faq_pointing_up" if verdict["bullish"] else "ta_faq_pointing_down"], the=the,
                word=(T["ta_bullish"] if verdict["bullish"] else T["ta_bearish"]).lower(),
                strength=T[f"ta_faq_strength_{verdict['strength']}"],
            ),
        },
        {"q": T["ta_faq_q_how"], "a": T["ta_faq_a_how"]},
    ]
    if weekly:
        faq.append({
            "q": T["ta_faq_q_weekly"].format(the=the),
            "a": T["ta_faq_a_weekly"].format(
                agree=weekly["agree"], total=weekly["total"], the=the,
                pointing=T["ta_faq_pointing_up" if weekly["bullish"] else "ta_faq_pointing_down"],
                word=T["ta_weekly_up" if weekly["bullish"] else "ta_weekly_down"],
            ),
        })
    if supports and resistances:
        faq.append({
            "q": T["ta_faq_q_levels"].format(the=the),
            "a": T["ta_faq_a_levels"].format(
                support=f"{supports[0]['price']:,.{d}f}", resistance=f"{resistances[0]['price']:,.{d}f}",
            ),
        })
    if forecast:
        end = forecast[-1]
        change = (end["c"] / last_close - 1) * 100
        faq.append({
            "q": T["ta_faq_q_forecast"].format(the=the),
            "a": T["ta_faq_a_forecast"].format(
                close=f"{end['c']:,.{d}f}", date=_long_date(end["x"], lang), change=f"{change:+.1f}%",
                lo=f"{end['band_lo']:,.{d}f}", hi=f"{end['band_hi']:,.{d}f}",
            ),
        })
    faq.append({"q": T["ta_faq_q_drivers"].format(the=the), "a": T[f"ta_asset_{key}_drivers"]})
    faq.append({"q": T["ta_faq_q_algo"], "a": T["ta_faq_a_algo"]})
    faq.append({"q": T["ta_faq_q_update"], "a": T["ta_faq_a_update"]})
    if lang != "en":
        # "de el" -> "del" (el oro, el NASDAQ 100, el EUR/USD).
        faq = [{"q": i["q"].replace(" de el ", " del "), "a": i["a"].replace(" de el ", " del ")} for i in faq]
    return faq


# ------------------------------------------------------------------------ main

def build_analysis(symbol=DEFAULT_SYMBOL, lang="es"):
    """Todo lo que pinta la pantalla (contexto de plantilla + payload JSON
    de la gráfica). Devuelve None si aún no hay velas diarias del activo."""
    T = get_translations(lang)
    symbol = symbol if symbol in ASSETS else DEFAULT_SYMBOL
    cfg = ASSETS[symbol]
    key = cfg["key"]
    digits = cfg["digits"]
    d = digits["level"]
    asset = Asset.objects.filter(symbol=symbol).first()
    if asset is None:
        return None
    df = price_bars_dataframe(asset, PriceBar.Timeframe.D1)
    if not cfg["weekends"]:
        # yfinance a veces trae una vela suelta en domingo (apertura de la
        # sesión asiática) en divisas/oro: cae dentro del salto de eje del
        # fin de semana y Plotly corta las líneas de las medias en ese punto.
        df = df[df.index.dayofweek < 5]
    if len(df) < 210:
        return None
    df = _indicator_frame(df)

    forecast, run = _forecast_bars(asset, df, cfg)
    close_now = float(df["close"].iloc[-1])
    forecast = [{**bar, "change_from_now": round((bar["c"] / close_now - 1) * 100, 2)} for bar in forecast]
    signals = _build_signals(df.dropna(subset=["sma200", "sma20", "rsi", "macd", "macd_signal"]), forecast, T, d)
    verdict = _verdict(signals, df)
    weekly = _weekly_read(asset)
    macd1h = _hourly_macd(asset, digits, T)
    levels = detect_levels(
        asset, lookback_days=cfg["level_bars"], max_levels=LEVEL_MAX, pivot_window=LEVEL_PIVOT_WINDOW,
    )

    last = df.iloc[-1]
    prev = df.iloc[-2]
    last_close = float(last["close"])
    change_pct = (last_close / float(prev["close"]) - 1) * 100

    def decorate(levels_list, kind):
        out = []
        for lv in levels_list:
            out.append({
                "price": lv["price"], "touches": lv["touches"],
                "distance_pct": round((lv["price"] / last_close - 1) * 100, 2),
                "strength": "strong" if lv["touches"] >= 3 else "medium" if lv["touches"] == 2 else "light",
                "kind": kind,
            })
        return out

    supports = decorate(levels["supports"], "support")
    resistances = decorate(levels["resistances"], "resistance")
    supports.sort(key=lambda lv: -lv["price"])      # el más cercano (más alto) primero
    resistances.sort(key=lambda lv: lv["price"])    # el más cercano (más bajo) primero

    chart_df = df.tail(CHART_BARS)
    try:
        direction_test = _holdout_direction_accuracy(asset, run) if run else None
    except Exception:  # extra informativo: nunca debe romper la pantalla
        logger.exception("No se pudo calcular el acierto de dirección del modelo diario")
        direction_test = None

    payload = {
        "bars": {
            "x": [_iso(t) for t in chart_df.index],
            "o": [round(v, digits["price"]) for v in chart_df["open"]],
            "h": [round(v, digits["price"]) for v in chart_df["high"]],
            "l": [round(v, digits["price"]) for v in chart_df["low"]],
            "c": [round(v, digits["price"]) for v in chart_df["close"]],
            "v": [int(v) for v in chart_df["volume"]],
            "sma20": [_num(v, digits["price"]) for v in chart_df["sma20"]],
            "sma50": [_num(v, digits["price"]) for v in chart_df["sma50"]],
            "sma200": [_num(v, digits["price"]) for v in chart_df["sma200"]],
        },
        "forecast": forecast,
        "levels": {"supports": supports, "resistances": resistances},
        "last_close": round(last_close, digits["price"]),
        "digits": digits,
        "weekends": cfg["weekends"],
        "macd1h": macd1h["payload"] if macd1h else None,
        "asset_name": T[f"ta_asset_{key}_name"],
        "i18n": {
            "timeframe_short": T["ta_timeframe_short"],
            "macd_signal": T["ta_macdh_signal"], "macd_hist": T["ta_macdh_hist"],
            "open": T["ta_open"], "high": T["ta_high"], "low": T["ta_low"], "close": T["ta_close"],
            "volume": T["ta_volume"], "forecast": T["ta_forecast_label"], "support": T["ta_support_short"],
            "resistance": T["ta_resistance_short"], "touches": T["ta_touches"], "band": T["ta_band_label"],
            "price": T["ta_price_now"], "hint_forecast": T["ta_forecast_hint"],
        },
    }

    calendar = build_month_calendar(lang, key)
    next_event = calendar["upcoming_high"]
    if next_event is not None:
        days = calendar["upcoming_high_days"]
        next_event_when = (
            T["ta_today"] if days == 0 else T["ta_tomorrow"] if days == 1 else T["ta_in_days"].format(n=days)
        )
    else:
        next_event_when = ""

    return {
        "asset": asset,
        "symbol": symbol,
        "asset_name": T[f"ta_asset_{key}_name"],
        "asset_the": T[f"ta_asset_{key}_the"],
        "effect_label": T["ta_cal_effect"].format(name=T[f"ta_asset_{key}_name"]),
        "digits": digits,
        "as_of": df.index[-1],
        "verdict_word": T["ta_bullish"] if verdict["bullish"] else T["ta_bearish"],
        "agree_text": T["ta_signals_agree"].format(agree=verdict["agree"], total=verdict["total"]),
        "strength_text": T[f"ta_strength_{verdict['strength']}"],
        "cal_intro": T["ta_cal_intro"].format(the=T[f"ta_asset_{key}_the"]),
        "cal_title": T["ta_cal_title"].format(month=calendar["month_label"]),
        "cal_count": T["ta_cal_count"].format(count=calendar["month_count"], high=calendar["high_count"]),
        "next_event_when": next_event_when,
        "resistances_desc": sorted(resistances, key=lambda lv: -lv["price"]),
        "price": last_close,
        "change_pct": round(change_pct, 2),
        "verdict": verdict,
        "signals": signals,
        "supports": supports,
        "resistances": resistances,
        "forecast": forecast,
        "forecast_close": forecast[-1]["c"] if forecast else None,
        "forecast_change_pct": round((forecast[-1]["c"] / last_close - 1) * 100, 2) if forecast else None,
        "narrative": _narrative(
            verdict, {"supports": supports, "resistances": resistances}, last_close, forecast, lang,
            T[f"ta_asset_{key}_the"], d, weekly,
        ),
        "rsi": round(float(last["rsi"]), 1),
        "sma50_gap_pct": round((last_close / float(last["sma50"]) - 1) * 100, 2),
        "atr_pct": round(float(last["atr"]) / last_close * 100, 2),
        "model_mae": float(run.mae) if run else None,
        "direction_test": direction_test,
        "calendar": calendar,
        "macd1h": macd1h,
        "weekly": weekly,
        "weekly_chip": T["ta_weekly_chip"].format(
            word=(T["ta_bullish"] if weekly["bullish"] else T["ta_bearish"]), agree=weekly["agree"], total=weekly["total"],
        ) if weekly else "",
        "faq": _build_faq(T, lang, key, verdict, df.index[-1], supports, resistances, forecast, digits, last_close, weekly),
        "chart_payload": payload,
    }


def asset_tabs(active_symbol, lang="es"):
    """Pestañas del selector de activo (nombre localizado + tipo)."""
    T = get_translations(lang)
    return [
        {
            "symbol": symbol,
            "name": T[f"ta_asset_{cfg['key']}_name"],
            "kind": T[f"ta_asset_{cfg['key']}_kind"],
            "active": symbol == active_symbol,
        }
        for symbol, cfg in ASSETS.items()
    ]
