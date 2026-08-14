"""
scanner/charts.py

Descarga velas OHLC con yfinance para un ticker y arma un gráfico de
velas japonesas (verde/roja) + volumen + RSI con Plotly, usando los
mismos indicadores que el scanner diario (scanner/services.py).

Los resultados se cachean por símbolo+periodo para no volver a golpear
Yahoo Finance en cada request (por ejemplo, cada vez que alguien pasa
el mouse sobre un ticker en la tabla del scanner).
"""
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from django.core.cache import cache
from plotly.subplots import make_subplots
from ta.momentum import RSIIndicator
from ta.trend import MACD

from .fundamentals import get_fundamentals

INTERVALS = {
    "1m": {"label": "1 min", "yf_interval": "1m", "period": "5d"},
    "5m": {"label": "5 min", "yf_interval": "5m", "period": "1mo"},
    "30m": {"label": "30 min", "yf_interval": "30m", "period": "1mo"},
    "1h": {"label": "1 hora", "yf_interval": "60m", "period": "3mo"},
    "4h": {"label": "4 horas", "yf_interval": "60m", "period": "6mo", "resample": "4h"},
    "1d": {"label": "Diario", "yf_interval": "1d", "period": "1y"},
    "1wk": {"label": "Semanal", "yf_interval": "1wk", "period": "5y"},
    "1mo": {"label": "Mensual", "yf_interval": "1mo", "period": "max"},
}
DEFAULT_INTERVAL = "1d"

# Segundos de cache por periodo: los intradía cambian rápido, los largos casi no.
CACHE_TTL = {
    "1m": 60, "5m": 120, "30m": 300, "1h": 600, "4h": 900,
    "1d": 1800, "1wk": 3600, "1mo": 3600,
}
MINI_CHART_TTL = 300

COLORS = {
    "bg": "#171a21",
    "grid": "#262a33",
    "text": "#e6e8eb",
    "up": "#3ddc97",
    "down": "#e5484d",
}

CHART_LABELS = {
    "es": {
        "price": "Precio", "volume": "Volumen", "rsi": "RSI (14)", "macd": "MACD (12,26,9)", "max_20": "Máx. 20 periodos",
        "ref_current": "Precio actual", "ref_target": "Precio objetivo", "ref_quarter_low": "Mínimo del trimestre",
    },
    "en": {
        "price": "Price", "volume": "Volume", "rsi": "RSI (14)", "macd": "MACD (12,26,9)", "max_20": "20-period high",
        "ref_current": "Current price", "ref_target": "Target price", "ref_quarter_low": "Quarter low",
    },
}
QUARTER_LOOKBACK_DAYS = 91


def get_price_history(symbol: str, interval_key: str) -> pd.DataFrame:
    config = INTERVALS.get(interval_key, INTERVALS[DEFAULT_INTERVAL])
    data = yf.download(
        symbol,
        period=config["period"],
        interval=config["yf_interval"],
        progress=False,
        auto_adjust=True,
    )
    if data.empty:
        return data

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if "resample" in config:
        data = data.resample(config["resample"]).agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }).dropna()

    return data


def build_price_chart(symbol: str, interval_key: str, lang: str = "es") -> dict:
    interval_key = interval_key if interval_key in INTERVALS else DEFAULT_INTERVAL
    lang = lang if lang in CHART_LABELS else "es"
    cache_key = f"scanner:chart:{symbol}:{interval_key}:{lang}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = _compute_price_chart(symbol, interval_key, lang)
    if result["error"] is None:
        cache.set(cache_key, result, CACHE_TTL.get(interval_key, 300))
    return result


def _compute_price_chart(symbol: str, interval_key: str, lang: str = "es") -> dict:
    labels = CHART_LABELS.get(lang, CHART_LABELS["es"])
    error_no_data = {
        "es": f"No se pudo descargar el histórico de {symbol}.",
        "en": f"Could not download the price history for {symbol}.",
    }
    error_not_enough = {
        "es": "No hay suficientes datos para este periodo.",
        "en": "Not enough data for this period.",
    }
    try:
        data = get_price_history(symbol, interval_key)
    except Exception:
        return {"html": None, "error": error_no_data.get(lang, error_no_data["es"])}

    if data.empty or len(data) < 5:
        return {"html": None, "error": error_not_enough.get(lang, error_not_enough["es"])}

    rsi = RSIIndicator(data["Close"], window=14).rsi()
    macd_calc = MACD(data["Close"])
    macd_line = macd_calc.macd()
    macd_signal_line = macd_calc.macd_signal()
    macd_hist = macd_calc.macd_diff()
    avg_volume_20 = data["Volume"].rolling(20).mean()
    relative_volume = data["Volume"] / avg_volume_20
    high_20 = data["Close"].rolling(20).max().shift(1)
    breakout = bool(data["Close"].iloc[-1] > high_20.iloc[-1]) if pd.notna(high_20.iloc[-1]) else False

    current_price = float(data["Close"].iloc[-1])
    quarter_cutoff = data.index[-1] - pd.Timedelta(days=QUARTER_LOOKBACK_DAYS)
    quarter_data = data.loc[data.index >= quarter_cutoff]
    quarter_low = float(quarter_data["Low"].min()) if not quarter_data.empty else None

    target_price = None
    try:
        target_price = get_fundamentals(symbol, lang, include_summary=False).get("target_mean_price")
        target_price = float(target_price) if target_price else None
    except Exception:
        target_price = None

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.4, 0.15, 0.2, 0.25],
        subplot_titles=(labels["price"], labels["volume"], labels["rsi"], labels["macd"]),
        specs=[[{"secondary_y": True}], [{}], [{}], [{}]],
    )

    fig.add_trace(go.Candlestick(
        x=data.index, open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"],
        increasing_line_color=COLORS["up"], increasing_fillcolor=COLORS["up"],
        decreasing_line_color=COLORS["down"], decreasing_fillcolor=COLORS["down"],
        name=labels["price"],
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data.index, y=high_20, mode="lines", name=labels["max_20"],
        line=dict(color=COLORS["text"], width=1, dash="dot"), opacity=0.5,
    ), row=1, col=1)

    # Plotly no dibuja los ticks de un eje secundario si ningún trace lo
    # referencia, aunque esté configurado en el layout — este trace
    # invisible (mismos datos que el cierre) solo existe para forzar que
    # la escala de precio también se muestre a la derecha.
    fig.add_trace(go.Scatter(
        x=data.index, y=data["Close"], mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        showlegend=False, hoverinfo="skip",
    ), row=1, col=1, secondary_y=True)

    # Líneas de referencia sobre el precio: dónde está hoy, hasta dónde
    # ven los analistas que puede llegar, y el mínimo reciente (~3 meses)
    # como referencia de soporte. Ver chart_panel.html para la leyenda
    # que explica cada una en texto.
    fig.add_hline(
        y=current_price, row=1, col=1,
        line_dash="solid", line_color=COLORS["text"], line_width=1, opacity=0.6,
        annotation_text=f"{labels['ref_current']}: ${current_price:,.2f}",
        annotation_position="bottom right", annotation_font_size=10, annotation_font_color=COLORS["text"],
    )
    if target_price:
        fig.add_hline(
            y=target_price, row=1, col=1,
            line_dash="dash", line_color=COLORS["up"], line_width=1.5, opacity=0.8,
            annotation_text=f"{labels['ref_target']}: ${target_price:,.2f}",
            annotation_position="top right", annotation_font_size=10, annotation_font_color=COLORS["up"],
        )
    if quarter_low:
        fig.add_hline(
            y=quarter_low, row=1, col=1,
            line_dash="dot", line_color="#f5a623", line_width=1.5, opacity=0.8,
            annotation_text=f"{labels['ref_quarter_low']}: ${quarter_low:,.2f}",
            annotation_position="bottom left", annotation_font_size=10, annotation_font_color="#f5a623",
        )

    volume_colors = [
        COLORS["up"] if c >= o else COLORS["down"]
        for o, c in zip(data["Open"], data["Close"])
    ]
    fig.add_trace(go.Bar(
        x=data.index, y=data["Volume"], name=labels["volume"], marker_color=volume_colors, opacity=0.6,
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=data.index, y=rsi, mode="lines", name=labels["rsi"], line=dict(color="#f5a623", width=1.5),
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["down"], opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["up"], opacity=0.5, row=3, col=1)

    macd_hist_colors = [COLORS["up"] if v >= 0 else COLORS["down"] for v in macd_hist.fillna(0)]
    fig.add_trace(go.Bar(
        x=data.index, y=macd_hist, name="Histograma", marker_color=macd_hist_colors, opacity=0.5,
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=data.index, y=macd_line, mode="lines", name="MACD", line=dict(color=COLORS["text"], width=1.5),
    ), row=4, col=1)
    fig.add_trace(go.Scatter(
        x=data.index, y=macd_signal_line, mode="lines", name="Señal", line=dict(color="#f5a623", width=1.5),
    ), row=4, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text"], opacity=0.4, row=4, col=1)

    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        showlegend=False,
        margin=dict(l=40, r=50, t=40, b=20),
        height=880,
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 5):
        fig.update_xaxes(gridcolor=COLORS["grid"], row=i, col=1)
        fig.update_yaxes(gridcolor=COLORS["grid"], row=i, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)
    # Repite la escala de precio también a la derecha (mismo rango que
    # la izquierda), para no tener que mirar hacia el otro lado del
    # gráfico al comparar con las líneas de referencia.
    fig.update_yaxes(matches="y", showticklabels=True, gridcolor=COLORS["grid"], row=1, col=1, secondary_y=True)

    html = fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displaylogo": False, "responsive": True, "scrollZoom": True},
    )

    last_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else None
    last_rel_vol = relative_volume.dropna().iloc[-1] if not relative_volume.dropna().empty else None

    return {
        "html": html,
        "error": None,
        "last_price": round(current_price, 2),
        "last_rsi": round(float(last_rsi), 2) if last_rsi is not None else None,
        "last_relative_volume": round(float(last_rel_vol), 2) if last_rel_vol is not None else None,
        "breakout": breakout,
        "target_price": round(target_price, 2) if target_price else None,
        "quarter_low": round(quarter_low, 2) if quarter_low else None,
    }


def build_mini_chart(symbol: str, lang: str = "es") -> dict:
    """Velas diarias de los últimos ~3 meses, sin subplots, para el preview en hover."""
    lang = lang if lang in CHART_LABELS else "es"
    cache_key = f"scanner:minichart:{symbol}:{lang}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    error_load = {"es": "No se pudo cargar la gráfica.", "en": "Could not load the chart."}
    error_no_data = {"es": "No hay datos disponibles.", "en": "No data available."}

    try:
        data = get_price_history(symbol, "1d")
    except Exception:
        return {"html": None, "error": error_load.get(lang, error_load["es"])}

    if data.empty:
        return {"html": None, "error": error_no_data.get(lang, error_no_data["es"])}

    data = data.tail(60)

    fig = go.Figure(data=[go.Candlestick(
        x=data.index, open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"],
        increasing_line_color=COLORS["up"], increasing_fillcolor=COLORS["up"],
        decreasing_line_color=COLORS["down"], decreasing_fillcolor=COLORS["down"],
    )])
    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"], size=10),
        margin=dict(l=35, r=10, t=10, b=25),
        height=220,
        showlegend=False,
        xaxis_rangeslider_visible=False,
    )
    fig.update_xaxes(gridcolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"])

    html = fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )
    result = {"html": html, "error": None}
    cache.set(cache_key, result, MINI_CHART_TTL)
    return result
