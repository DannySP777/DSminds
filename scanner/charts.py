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


def build_price_chart(symbol: str, interval_key: str) -> dict:
    interval_key = interval_key if interval_key in INTERVALS else DEFAULT_INTERVAL
    cache_key = f"scanner:chart:{symbol}:{interval_key}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = _compute_price_chart(symbol, interval_key)
    if result["error"] is None:
        cache.set(cache_key, result, CACHE_TTL.get(interval_key, 300))
    return result


def _compute_price_chart(symbol: str, interval_key: str) -> dict:
    try:
        data = get_price_history(symbol, interval_key)
    except Exception:
        return {"html": None, "error": f"No se pudo descargar el histórico de {symbol}."}

    if data.empty or len(data) < 5:
        return {"html": None, "error": "No hay suficientes datos para este periodo."}

    rsi = RSIIndicator(data["Close"], window=14).rsi()
    avg_volume_20 = data["Volume"].rolling(20).mean()
    relative_volume = data["Volume"] / avg_volume_20
    high_20 = data["Close"].rolling(20).max().shift(1)
    breakout = bool(data["Close"].iloc[-1] > high_20.iloc[-1]) if pd.notna(high_20.iloc[-1]) else False

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.55, 0.2, 0.25],
        subplot_titles=("Precio", "Volumen", "RSI (14)"),
    )

    fig.add_trace(go.Candlestick(
        x=data.index, open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"],
        increasing_line_color=COLORS["up"], increasing_fillcolor=COLORS["up"],
        decreasing_line_color=COLORS["down"], decreasing_fillcolor=COLORS["down"],
        name="Precio",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=data.index, y=high_20, mode="lines", name="Máx. 20 periodos",
        line=dict(color=COLORS["text"], width=1, dash="dot"), opacity=0.5,
    ), row=1, col=1)

    volume_colors = [
        COLORS["up"] if c >= o else COLORS["down"]
        for o, c in zip(data["Open"], data["Close"])
    ]
    fig.add_trace(go.Bar(
        x=data.index, y=data["Volume"], name="Volumen", marker_color=volume_colors, opacity=0.6,
    ), row=2, col=1)

    fig.add_trace(go.Scatter(
        x=data.index, y=rsi, mode="lines", name="RSI (14)", line=dict(color="#f5a623", width=1.5),
    ), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["down"], opacity=0.5, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["up"], opacity=0.5, row=3, col=1)

    fig.update_layout(
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        showlegend=False,
        margin=dict(l=40, r=20, t=40, b=20),
        height=680,
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 4):
        fig.update_xaxes(gridcolor=COLORS["grid"], row=i, col=1)
        fig.update_yaxes(gridcolor=COLORS["grid"], row=i, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)

    html = fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displaylogo": False, "responsive": True},
    )

    last_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else None
    last_rel_vol = relative_volume.dropna().iloc[-1] if not relative_volume.dropna().empty else None

    return {
        "html": html,
        "error": None,
        "last_price": round(float(data["Close"].iloc[-1]), 2),
        "last_rsi": round(float(last_rsi), 2) if last_rsi is not None else None,
        "last_relative_volume": round(float(last_rel_vol), 2) if last_rel_vol is not None else None,
        "breakout": breakout,
    }


def build_mini_chart(symbol: str) -> dict:
    """Velas diarias de los últimos ~3 meses, sin subplots, para el preview en hover."""
    cache_key = f"scanner:minichart:{symbol}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        data = get_price_history(symbol, "1d")
    except Exception:
        return {"html": None, "error": "No se pudo cargar la gráfica."}

    if data.empty:
        return {"html": None, "error": "No hay datos disponibles."}

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
