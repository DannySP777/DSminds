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
- MACD(12,26,9) diario: momentum de tendencia
- Fundamentales (target de analistas, deuda, liquidez), vía
  fundamentals.get_fundamentals, usados tanto para mostrar en pantalla
  como para el score (ver _score)
"""
from datetime import date

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange

from .fundamentals import get_fundamentals

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

        macd_calc = MACD(close)
        macd_line = macd_calc.macd().iloc[-1]
        macd_signal_line = macd_calc.macd_signal().iloc[-1]
        macd_valid = pd.notna(macd_line) and pd.notna(macd_signal_line)
        # "Zona de compra": cruce alcista (MACD > señal) confirmado por
        # una tendencia de fondo ya positiva (ambas líneas por encima de
        # cero), no solo un giro reciente todavía en terreno negativo.
        macd_bullish = bool(
            macd_valid and macd_line > macd_signal_line and macd_line > 0 and macd_signal_line > 0
        )

        current_price = float(close.iloc[-1])
        fundamentals = get_fundamentals(symbol, include_summary=False)
        target_price = fundamentals.get("target_mean_price")
        upside_pct = (
            round((target_price / current_price - 1) * 100, 1)
            if target_price else None
        )
        debt_to_equity = fundamentals.get("debt_to_equity")
        current_ratio = fundamentals.get("current_ratio")

        score = _score(
            rsi=rsi,
            macd_bullish=macd_bullish,
            relative_volume=relative_volume,
            breakout=breakout,
            above_ma200=above_ma200,
            relative_strength=relative_strength,
            upside_pct=upside_pct,
            debt_to_equity=debt_to_equity,
            current_ratio=current_ratio,
        )

        results.append({
            "symbol": symbol,
            "price": round(current_price, 2),
            "rsi": round(float(rsi), 2),
            "relative_volume": round(float(relative_volume), 2),
            "breakout": breakout,
            "ma200": round(ma200, 2) if ma200 is not None else None,
            "above_ma200": above_ma200,
            "atr": round(float(atr), 2) if atr_valid else None,
            "stop_loss": stop_loss,
            "relative_strength": relative_strength,
            "macd": round(float(macd_line), 4) if macd_valid else None,
            "macd_signal": round(float(macd_signal_line), 4) if macd_valid else None,
            "macd_bullish": macd_bullish,
            "target_price": target_price,
            "market_cap": fundamentals.get("market_cap"),
            "market_cap_display": fundamentals.get("market_cap_display") or "",
            "trailing_pe": fundamentals.get("trailing_pe"),
            "peg_ratio": fundamentals.get("peg_ratio"),
            "debt_to_equity": debt_to_equity,
            "current_ratio": current_ratio,
            "exchange": fundamentals.get("exchange") or "",
            "score": score,
        })

    return sorted(results, key=lambda r: r["score"], reverse=True)


def _score(
    rsi,
    macd_bullish,
    relative_volume,
    breakout,
    above_ma200,
    relative_strength,
    upside_pct,
    debt_to_equity,
    current_ratio,
) -> float:
    """
    Score 0-100. Los 5 criterios que definen una "buena oportunidad"
    pesan el 70% del score; el resto son las señales técnicas que ya
    existían, con menor peso:

    - Upside del precio objetivo de analistas vs. precio actual, hasta
      +25% (o más): 20
    - RSI en zona de compra (<50, ni sobrecomprado ni en plena caída
      libre de fondo): 15
    - MACD diario en zona de compra (línea por encima de la señal, y
      ambas por encima de cero): 15
    - No sobreendeudada (Deuda/Patrimonio < 100%): 10
    - Con liquidez (Current Ratio > 1): 10
    - Por encima de la MA200 (tendencia de fondo alcista): 10
    - Fuerza relativa vs. S&P 500 (hasta +10pp de outperformance): 10
    - Ruptura de rango de 20 días: 5
    - Volumen relativo (hasta 3x): 5
    """
    score = 0.0

    if upside_pct is not None:
        score += min(max(upside_pct, 0) / 25 * 20, 20)

    if rsi is not None and rsi < 50:
        score += 15

    if macd_bullish:
        score += 15

    if debt_to_equity is not None and debt_to_equity < 100:
        score += 10

    if current_ratio is not None and current_ratio > 1:
        score += 10

    if above_ma200:
        score += 10

    if relative_strength is not None:
        score += max(0, min(relative_strength, 10))

    if breakout:
        score += 5

    score += min(relative_volume, 3) * (5 / 3)

    return round(max(min(score, 100), 0), 2)


def save_scan_results(symbols: list[str]) -> int:
    """
    Corre el scan sobre `symbols` y guarda un ScanResult por cada uno
    para la fecha de hoy. Compartida entre el comando run_scan (universo
    completo, programado) y la vista que agrega un ticker individual al
    scanner (scanner/views.py:add_ticker) — misma lógica, un solo lugar.
    """
    from .models import ScanResult, Ticker

    results = run_daily_scan(symbols)
    today = date.today()

    saved = 0
    for r in results:
        ticker, _ = Ticker.objects.get_or_create(symbol=r["symbol"])
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
                "macd": r["macd"],
                "macd_signal": r["macd_signal"],
                "macd_bullish": r["macd_bullish"],
                "current_ratio": r["current_ratio"],
                "target_price": r["target_price"],
                "market_cap": r["market_cap"],
                "market_cap_display": r["market_cap_display"],
                "trailing_pe": r["trailing_pe"],
                "peg_ratio": r["peg_ratio"],
                "debt_to_equity": r["debt_to_equity"],
                "exchange": r["exchange"],
                "score": r["score"],
            },
        )
        saved += 1

    return saved
