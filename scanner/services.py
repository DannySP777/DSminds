"""
Lógica principal del scanner diario: descarga precios con yfinance y
calcula, para cada ticker:

- RSI(14) y volumen relativo (ya existían)
- Ruptura del rango de los últimos 20 días (ya existía)
- MA200: filtro de tendencia de fondo (¿está por encima de su media de 200
  días?), para no confundir un rebote de corto plazo con una tendencia real
- ATR(14): volatilidad, usada para sugerir un stop-loss
- Fuerza relativa (RS) vs. S&P 500: ¿le está ganando al mercado o solo
  sube porque el mercado entero sube?
"""
from datetime import date

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# Universo del scanner. USD/NYSE+NASDAQ únicamente a propósito: tickers
# de Tokio/Londres (ej. "7203.T", "HSBA.L") cotizan en yenes/libras, lo
# que rompería el filtro de precio en USD sin conversión de moneda.
DEFAULT_TICKERS = [
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "NFLX", "AVGO",
    # Financieras
    "JPM", "BAC", "WFC", "GS", "V", "MA",
    # Salud
    "JNJ", "PFE", "UNH", "MRK",
    # Consumo
    "WMT", "PG", "KO", "PEP", "MCD", "NKE", "HD", "DIS",
    # Energía / industriales
    "XOM", "CVX", "BA", "GE", "CAT",
    # Telecom / tecnología establecida
    "T", "VZ", "INTC", "CSCO", "ORCL", "IBM", "QCOM",
    # Precio bajo / alta volatilidad
    "F", "SOFI", "NIO", "PLTR", "RIVN", "LCID", "SNAP", "PINS", "LYFT", "CCL", "AAL", "SIRI", "KVUE",
    # Otros de interés
    "UBER", "ABNB", "COIN", "RIOT", "MARA", "BABA", "TSM",
]

BENCHMARK = "SPY"
HISTORY_PERIOD = "2y"
RS_LOOKBACK_DAYS = 63  # ~3 meses de trading


def _download(symbol: str):
    data = yf.download(symbol, period=HISTORY_PERIOD, interval="1d", progress=False, auto_adjust=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


def _period_return(close, lookback: int):
    if len(close) <= lookback:
        return None
    start = close.iloc[-lookback - 1]
    end = close.iloc[-1]
    if not start:
        return None
    return float((end / start - 1) * 100)


def run_daily_scan(tickers: list[str]) -> list[dict]:
    benchmark_data = _download(BENCHMARK)
    benchmark_return = None
    if not benchmark_data.empty:
        benchmark_return = _period_return(benchmark_data["Close"], RS_LOOKBACK_DAYS)

    results = []
    for symbol in tickers:
        data = _download(symbol)
        if data.empty or len(data) < 20:
            continue

        close = data["Close"]
        high = data["High"]
        low = data["Low"]
        volume = data["Volume"]

        rsi = RSIIndicator(close).rsi().iloc[-1]
        avg_volume_20d = volume.iloc[-21:-1].mean()
        relative_volume = volume.iloc[-1] / avg_volume_20d if avg_volume_20d else 0

        high_20d = close.iloc[-21:-1].max()
        breakout = bool(close.iloc[-1] > high_20d)

        ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
        above_ma200 = bool(ma200 is not None and close.iloc[-1] > ma200)

        atr = AverageTrueRange(high, low, close, window=14).average_true_range().iloc[-1]
        atr_valid = pd.notna(atr)
        stop_loss = round(float(close.iloc[-1] - 1.5 * atr), 2) if atr_valid else None

        stock_return = _period_return(close, RS_LOOKBACK_DAYS)
        relative_strength = None
        if stock_return is not None and benchmark_return is not None:
            relative_strength = round(stock_return - benchmark_return, 2)

        score = _score(rsi, relative_volume, breakout, above_ma200, relative_strength)

        results.append({
            "symbol": symbol,
            "price": round(float(close.iloc[-1]), 2),
            "rsi": round(float(rsi), 2),
            "relative_volume": round(float(relative_volume), 2),
            "breakout": breakout,
            "ma200": round(ma200, 2) if ma200 is not None else None,
            "above_ma200": above_ma200,
            "atr": round(float(atr), 2) if atr_valid else None,
            "stop_loss": stop_loss,
            "relative_strength": relative_strength,
            "score": score,
        })

    return sorted(results, key=lambda r: r["score"], reverse=True)


def _score(rsi, relative_volume, breakout, above_ma200, relative_strength) -> float:
    """
    Score 0-100:
    - RSI en zona de impulso (50-70): 25
    - Volumen relativo (hasta 3x): 20
    - Ruptura de rango de 20 días: 10
    - Por encima de la MA200 (tendencia de fondo alcista): 25
    - Fuerza relativa vs. S&P 500 (hasta +10pp de outperformance): 20
    """
    score = 0.0
    if 50 <= rsi <= 70:
        score += 25
    elif rsi > 70:
        score += 10

    score += min(relative_volume, 3) * (20 / 3)

    if breakout:
        score += 10

    if above_ma200:
        score += 25

    if relative_strength is not None:
        score += max(0, min(relative_strength, 10)) * 2

    return round(max(min(score, 100), 0), 2)


def save_scan_results(symbols: list[str]) -> int:
    """
    Corre el scan sobre `symbols` y guarda un ScanResult por cada uno
    para la fecha de hoy. Compartida entre el comando run_scan (universo
    completo, programado) y la vista que agrega un ticker individual al
    scanner (scanner/views.py:add_ticker) — misma lógica, un solo lugar.
    """
    from .fundamentals import get_fundamentals
    from .models import ScanResult, Ticker

    results = run_daily_scan(symbols)
    today = date.today()

    saved = 0
    for r in results:
        ticker, _ = Ticker.objects.get_or_create(symbol=r["symbol"])
        fundamentals = get_fundamentals(r["symbol"], include_summary=False)
        ScanResult.objects.update_or_create(
            ticker=ticker,
            date=today,
            defaults={
                "price": r["price"],
                "rsi": r["rsi"],
                "relative_volume": r["relative_volume"],
                "breakout": r["breakout"],
                "ma200": r["ma200"],
                "above_ma200": r["above_ma200"],
                "atr": r["atr"],
                "stop_loss": r["stop_loss"],
                "relative_strength": r["relative_strength"],
                "target_price": fundamentals.get("target_mean_price"),
                "market_cap": fundamentals.get("market_cap"),
                "market_cap_display": fundamentals.get("market_cap_display") or "",
                "trailing_pe": fundamentals.get("trailing_pe"),
                "peg_ratio": fundamentals.get("peg_ratio"),
                "debt_to_equity": fundamentals.get("debt_to_equity"),
                "exchange": fundamentals.get("exchange") or "",
                "score": r["score"],
            },
        )
        saved += 1

    return saved
