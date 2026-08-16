"""
Gráficas de DSprofeta, en paneles separados:

- build_prediction_chart: velas japonesas con el histórico real (hasta
  100 velas, elegidas por el usuario) más la predicción sobre el precio
  de cierre — el valor predicho (naranja punteado) y, una vez se
  resuelve, el valor real (verde), superpuestos y distinguidos por
  color/estilo (no por espacio reservado en el eje de tiempo).
- build_rsi_chart / build_macd_chart: gráficas aparte para esos dos
  indicadores, mismo eje de tiempo/ventana que la de precio, mismo
  patrón visual que scanner/charts.py.

Se arman a partir de PriceBar/Prediction ya guardados en la base (no
vuelven a golpear yfinance), cacheadas brevemente igual que scanner/charts.py.
"""
import pandas as pd
import plotly.graph_objects as go
from django.core.cache import cache
from plotly.subplots import make_subplots
from ta.momentum import RSIIndicator
from ta.trend import MACD

from config.translations import get_translations

from .models import PriceBar, Prediction

COLORS = {
    "bg": "#171a21",
    "grid": "#262a33",
    "text": "#e6e8eb",
    "up": "#3ddc97",
    "down": "#e5484d",
    "predicted": "#f5a623",
    "actual": "#3ddc97",
}

CACHE_TTL = 60
MAX_HISTORY_BARS = 100
DEFAULT_HISTORY_BARS = 50
INDICATOR_WARMUP_BARS = 60  # velas extra hacia atrás para que RSI(14)/MACD(12,26,9) no arranquen en NaN

# El mercado no opera en fin de semana — sin esto, el eje de tiempo (de
# fecha continua) reserva espacio en blanco entre el viernes y el lunes
# porque no hay velas ahí, y se ve como un hueco roto en la gráfica.
WEEKEND_RANGEBREAKS = [{"bounds": ["sat", "mon"]}]


def clamp_history_bars(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = DEFAULT_HISTORY_BARS
    return max(1, min(value, MAX_HISTORY_BARS))


def _cache_key(kind, asset, timeframe, history_bars, lang):
    return f"dsprofeta:chart:{kind}:{asset.symbol}:{timeframe}:{history_bars}:{lang}"


def invalidate_prediction_chart(asset, timeframe, history_bars=DEFAULT_HISTORY_BARS):
    """Se llama al crear/resolver una predicción para que el próximo request
    no muestre el resultado cacheado desactualizado (ver views.predict)."""
    history_bars = clamp_history_bars(history_bars)
    for kind in ("price", "rsi", "macd"):
        for lang in ("es", "en"):
            cache.delete(_cache_key(kind, asset, timeframe, history_bars, lang))


def _load_series(asset, timeframe, history_bars):
    """Datos + indicadores compartidos por las 3 gráficas: se calculan una
    sola vez y cada build_*_chart arma su propia figura a partir de esto."""
    raw_bars = list(
        PriceBar.objects.filter(asset=asset, timeframe=timeframe)
        .order_by("-timestamp")[: history_bars + INDICATOR_WARMUP_BARS]
    )
    raw_bars.reverse()
    if not raw_bars:
        return None

    closes_full = pd.Series([float(b.close) for b in raw_bars])
    rsi_full = RSIIndicator(closes_full, window=14).rsi()
    macd_calc = MACD(closes_full)
    macd_line_full = macd_calc.macd()
    macd_signal_full = macd_calc.macd_signal()
    macd_hist_full = macd_calc.macd_diff()

    bars = raw_bars[-history_bars:]
    slice_from = len(raw_bars) - len(bars)

    x = [b.timestamp for b in bars]
    t_start, t_now = x[0], x[-1]

    return {
        "x": x,
        "opens": [float(b.open) for b in bars],
        "highs": [float(b.high) for b in bars],
        "lows": [float(b.low) for b in bars],
        "closes": [float(b.close) for b in bars],
        "rsi": rsi_full.iloc[slice_from:].reset_index(drop=True),
        "macd_line": macd_line_full.iloc[slice_from:].reset_index(drop=True),
        "macd_signal": macd_signal_full.iloc[slice_from:].reset_index(drop=True),
        "macd_hist": macd_hist_full.iloc[slice_from:].reset_index(drop=True),
        "t_start": t_start, "t_now": t_now,
    }


def _base_layout(height, xaxis_range=None, right_margin=30):
    layout = dict(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        margin=dict(l=40, r=right_margin, t=30, b=30),
        height=height,
        legend=dict(orientation="h", y=1.12),
        xaxis_rangeslider_visible=False,
    )
    if xaxis_range is not None:
        layout["xaxis_range"] = xaxis_range
    return layout


def _to_html(fig):
    return fig.to_html(
        full_html=False, include_plotlyjs=False,
        config={"displaylogo": False, "responsive": True},
    )


# ---------------------------------------------------------------- precio

def build_prediction_chart(asset, timeframe, history_bars=DEFAULT_HISTORY_BARS, lang="es"):
    history_bars = clamp_history_bars(history_bars)
    cache_key = _cache_key("price", asset, timeframe, history_bars, lang)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = _compute_prediction_chart(asset, timeframe, history_bars, lang)
    cache.set(cache_key, result, CACHE_TTL)
    return result


def _compute_prediction_chart(asset, timeframe, history_bars, lang):
    T = get_translations(lang)
    all_predictions = list(
        Prediction.objects.filter(asset=asset, timeframe=timeframe)
        .order_by("target_time")
        .values("target_time", "predicted_close", "actual_close")
    )
    resolved = [p for p in all_predictions if p["actual_close"] is not None]
    mae = None
    if resolved:
        errors = [abs(float(p["actual_close"]) - float(p["predicted_close"])) for p in resolved]
        mae = sum(errors) / len(errors)
    stats = {
        "n_predictions": len(all_predictions),
        "n_resolved": len(resolved),
        "mae": round(mae, 4) if mae is not None else None,
        "history_bars": history_bars,
        "last_close": None,
    }

    series = _load_series(asset, timeframe, history_bars)
    if series is None:
        return {"html": None, "error": T["dsp_chart_no_history"], **stats}

    x, t_start, t_now = series["x"], series["t_start"], series["t_now"]
    stats["last_close"] = series["closes"][-1]

    # Deja siempre ~20% del ancho total del gráfico libre a la derecha para
    # que la predicción generada tenga espacio donde dibujarse, sin llegar
    # a reservar la mitad como antes. 20% del total equivale a 25% del
    # ancho del histórico mostrado (si H es el histórico y E lo extra,
    # E = 0.2*(H+E) → E = 0.25*H).
    span = t_now - t_start
    t_future_end = t_now + span * 0.25 if span.total_seconds() > 0 else t_now

    fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Candlestick(
        x=x, open=series["opens"], high=series["highs"], low=series["lows"], close=series["closes"],
        increasing_line_color=COLORS["up"], increasing_fillcolor=COLORS["up"],
        decreasing_line_color=COLORS["down"], decreasing_fillcolor=COLORS["down"],
        name=T["dsp_trace_history"],
    ))

    # Se muestra cualquier predicción cuyo target_time caiga desde el
    # inicio del histórico mostrado en adelante — las del backtest son
    # retrospectivas (simulan velas ya pasadas) y quedan dentro de ese
    # rango; una futura (predict_next) cae dentro del 20% reservado.
    # Predicción y real se distinguen por color/estilo, no por dividir el
    # gráfico a la mitad.
    visible_predictions = [p for p in all_predictions if p["target_time"] >= t_start]
    if visible_predictions:
        px = [p["target_time"] for p in visible_predictions]
        predicted = [float(p["predicted_close"]) for p in visible_predictions]
        actual = [float(p["actual_close"]) if p["actual_close"] is not None else None for p in visible_predictions]
        fig.add_trace(go.Scatter(
            x=px, y=predicted, mode="lines+markers", name=T["dsp_trace_predicted"],
            line=dict(color=COLORS["predicted"], width=2, dash="dot"),
            marker=dict(size=18, symbol="star", color="#ffffff", line=dict(color=COLORS["predicted"], width=2)),
        ))
        fig.add_trace(go.Scatter(
            x=px, y=actual, mode="lines+markers", name=T["dsp_trace_actual"],
            line=dict(color=COLORS["actual"], width=2),
            marker=dict(size=11, color=COLORS["actual"], line=dict(color="#ffffff", width=1.5)),
            connectgaps=False,
        ))

    # Plotly no dibuja los ticks del eje secundario si ningún trace lo
    # referencia — este trace invisible (mismos datos que el cierre) solo
    # existe para forzar que la escala de precio se repita a la derecha.
    fig.add_trace(go.Scatter(
        x=x, y=series["closes"], mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        showlegend=False, hoverinfo="skip",
    ), secondary_y=True)

    # Línea vertical marcando la última vela real disponible ("ahora") y
    # línea horizontal en el último precio real, para comparar de un
    # vistazo dónde está el precio actual contra la predicción.
    fig.add_vline(x=t_now, line_dash="dash", line_color=COLORS["text"], opacity=0.4)
    fig.add_hline(
        y=stats["last_close"], line_dash="dash", line_color="#f5d423", line_width=2, opacity=0.9,
        annotation_text=f"{stats['last_close']:,.2f}", annotation_position="right",
        annotation_font_color="#f5d423",
    )

    fig.update_layout(**_base_layout(460, xaxis_range=[t_start, t_future_end], right_margin=50))
    fig.update_xaxes(gridcolor=COLORS["grid"], rangebreaks=WEEKEND_RANGEBREAKS)
    fig.update_yaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(matches="y", showticklabels=True, gridcolor=COLORS["grid"], secondary_y=True)

    return {"html": _to_html(fig), "error": None, **stats}


# ------------------------------------------------------------------- rsi

def build_rsi_chart(asset, timeframe, history_bars=DEFAULT_HISTORY_BARS, lang="es"):
    history_bars = clamp_history_bars(history_bars)
    cache_key = _cache_key("rsi", asset, timeframe, history_bars, lang)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    T = get_translations(lang)
    series = _load_series(asset, timeframe, history_bars)
    if series is None:
        result = {"html": None, "error": T["dsp_chart_no_history"], "last_rsi": None}
        cache.set(cache_key, result, CACHE_TTL)
        return result

    x, rsi = series["x"], series["rsi"]
    last_rsi = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=rsi, mode="lines", name=T["dsp_trace_rsi"], line=dict(color="#f5a623", width=1.5)))
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["down"], opacity=0.5)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["up"], opacity=0.5)
    fig.add_vline(x=series["t_now"], line_dash="dash", line_color=COLORS["text"], opacity=0.4)
    fig.update_layout(**_base_layout(280))
    fig.update_yaxes(range=[0, 100], gridcolor=COLORS["grid"])
    fig.update_xaxes(gridcolor=COLORS["grid"], rangebreaks=WEEKEND_RANGEBREAKS)

    result = {"html": _to_html(fig), "error": None, "last_rsi": last_rsi}
    cache.set(cache_key, result, CACHE_TTL)
    return result


# ------------------------------------------------------------------ macd

def build_macd_chart(asset, timeframe, history_bars=DEFAULT_HISTORY_BARS, lang="es"):
    history_bars = clamp_history_bars(history_bars)
    cache_key = _cache_key("macd", asset, timeframe, history_bars, lang)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    T = get_translations(lang)
    series = _load_series(asset, timeframe, history_bars)
    if series is None:
        result = {"html": None, "error": T["dsp_chart_no_history"], "last_macd_line": None, "last_macd_signal": None}
        cache.set(cache_key, result, CACHE_TTL)
        return result

    x = series["x"]
    macd_line, macd_signal, macd_hist = series["macd_line"], series["macd_signal"], series["macd_hist"]
    last_macd_line = float(macd_line.iloc[-1]) if pd.notna(macd_line.iloc[-1]) else None
    last_macd_signal = float(macd_signal.iloc[-1]) if pd.notna(macd_signal.iloc[-1]) else None

    macd_hist_colors = [COLORS["up"] if v >= 0 else COLORS["down"] for v in macd_hist.fillna(0)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=macd_hist, name=T["dsp_trace_histogram"], marker_color=macd_hist_colors, opacity=0.5))
    fig.add_trace(go.Scatter(x=x, y=macd_line, mode="lines", name=T["dsp_trace_macd"], line=dict(color=COLORS["text"], width=1.5)))
    fig.add_trace(go.Scatter(x=x, y=macd_signal, mode="lines", name=T["dsp_trace_signal"], line=dict(color="#f5a623", width=1.5)))
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text"], opacity=0.4)
    fig.add_vline(x=series["t_now"], line_dash="dash", line_color=COLORS["text"], opacity=0.4)
    fig.update_layout(**_base_layout(300))
    fig.update_xaxes(gridcolor=COLORS["grid"], rangebreaks=WEEKEND_RANGEBREAKS)
    fig.update_yaxes(gridcolor=COLORS["grid"])

    result = {
        "html": _to_html(fig), "error": None,
        "last_macd_line": last_macd_line, "last_macd_signal": last_macd_signal,
    }
    cache.set(cache_key, result, CACHE_TTL)
    return result
