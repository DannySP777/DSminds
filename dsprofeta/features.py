"""
Feature engineering para DSprofeta.

Todo lo que se calcula acá es "causal": para la fila que representa el
instante t, solo se usan datos disponibles hasta t (nunca del futuro).
Esto es lo que evita fuga de información (data leakage) al entrenar.
"""
from datetime import timedelta

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import AverageTrueRange

from .models import EconomicEvent, NewsHeadline, PriceBar

FIB_RATIOS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)

# Categorías de calendario económico que más mueven índices/forex/oro:
# decisiones de tasas de interés (Fed/FOMC), PMI, y datos de empleo de EE.UU.
# Se detectan por palabras clave en el título del evento (Finnhub no trae un
# campo de categoría aparte).
ECON_CATEGORY_KEYWORDS = {
    "econ_rate_decision_nearby": ["interest rate", "fed funds", "rate decision", "fomc"],
    "econ_pmi_nearby": ["pmi", "purchasing managers"],
    "econ_employment_nearby": ["non-farm", "nonfarm", "payrolls", "unemployment", "jobless claims", "employment change"],
}

FEATURE_COLUMNS = [
    "close", "rsi", "macd_line", "macd_signal", "atr", "sma_20",
    "fib_position_pct", "fib_distance_pct",
    "econ_high_impact_before", "econ_high_impact_after",
    "econ_minutes_to_nearest_high_impact", "econ_avg_surprise",
    *ECON_CATEGORY_KEYWORDS.keys(),
    "news_headline_count",
]


def price_bars_dataframe(asset, timeframe):
    rows = list(
        PriceBar.objects.filter(asset=asset, timeframe=timeframe)
        .order_by("timestamp")
        .values("timestamp", "open", "high", "low", "close", "volume")
    )
    if not rows:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"]).set_index("timestamp")
    df = pd.DataFrame(rows)
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype(float)
    df["volume"] = df["volume"].fillna(0).astype(float)
    return df.set_index("timestamp")


def _add_technical_columns(df, lookback):
    df["rsi"] = RSIIndicator(df["close"]).rsi()
    macd_calc = MACD(df["close"])
    df["macd_line"] = macd_calc.macd()
    df["macd_signal"] = macd_calc.macd_signal()
    df["atr"] = AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    df["sma_20"] = SMAIndicator(df["close"], window=20).sma_indicator()

    swing_high = df["high"].rolling(lookback).max()
    swing_low = df["low"].rolling(lookback).min()
    rng = (swing_high - swing_low).replace(0, pd.NA)

    df["fib_position_pct"] = (df["close"] - swing_low) / rng * 100

    level_distances = pd.concat(
        {ratio: (swing_high - rng * ratio).sub(df["close"]).abs() for ratio in FIB_RATIOS},
        axis=1,
    )
    df["fib_distance_pct"] = level_distances.min(axis=1) / df["close"] * 100
    return df


def _load_economic_events(start, end):
    return list(
        EconomicEvent.objects.filter(event_time__gte=start, event_time__lte=end)
        .values("event_time", "impact", "actual", "forecast", "title")
    )


def _load_news_headlines(start, end, symbol):
    return list(
        NewsHeadline.objects.filter(
            published_at__gte=start, published_at__lte=end, related_symbols__icontains=symbol,
        ).values("published_at")
    )


def _economic_event_features(current_time, events, window_hours=24):
    window_start = current_time - timedelta(hours=window_hours)
    window_end = current_time + timedelta(hours=window_hours)
    count_before, count_after, nearest_minutes = 0, 0, None
    surprises = []
    category_flags = {key: 0 for key in ECON_CATEGORY_KEYWORDS}

    for event in events:
        t = event["event_time"]
        if t < window_start or t > window_end:
            continue
        if event["actual"] is not None and event["forecast"] not in (None, 0):
            surprises.append(float((event["actual"] - event["forecast"]) / abs(event["forecast"])))

        title = (event["title"] or "").lower()
        for feature_key, keywords in ECON_CATEGORY_KEYWORDS.items():
            if any(k in title for k in keywords):
                category_flags[feature_key] = 1

        if event["impact"] != "high":
            continue
        diff_minutes = abs((t - current_time).total_seconds()) / 60
        if nearest_minutes is None or diff_minutes < nearest_minutes:
            nearest_minutes = diff_minutes
        if t <= current_time:
            count_before += 1
        else:
            count_after += 1

    return {
        "econ_high_impact_before": count_before,
        "econ_high_impact_after": count_after,
        "econ_minutes_to_nearest_high_impact": nearest_minutes if nearest_minutes is not None else window_hours * 60,
        "econ_avg_surprise": sum(surprises) / len(surprises) if surprises else 0.0,
        **category_flags,
    }


def _news_features(current_time, headlines, window_hours=6):
    window_start = current_time - timedelta(hours=window_hours)
    count = sum(1 for h in headlines if window_start <= h["published_at"] <= current_time)
    return {"news_headline_count": count}


def _iter_feature_samples(asset, timeframe, lookback=100):
    """
    Genera, para cada vela con suficiente historial previo, sus features
    causales + el resultado real de la vela siguiente (target). Es la
    base tanto de build_feature_frame (entrenamiento) como de
    build_backtest_samples (simulación, ver management/commands/backtest_predictions.py).
    """
    df = price_bars_dataframe(asset, timeframe)
    if len(df) < lookback + 2:
        return

    df = _add_technical_columns(df, lookback)
    events = _load_economic_events(df.index[0] - timedelta(hours=24), df.index[-1] + timedelta(hours=24))
    headlines = _load_news_headlines(df.index[0], df.index[-1], asset.symbol)

    timestamps = df.index.to_list()
    for i in range(lookback, len(df) - 1):
        current_time = timestamps[i]
        current_close = float(df["close"].iloc[i])
        next_close = float(df["close"].iloc[i + 1])

        row = df.iloc[i][["close", "rsi", "macd_line", "macd_signal", "atr", "sma_20",
                           "fib_position_pct", "fib_distance_pct"]].to_dict()
        row.update(_economic_event_features(current_time, events))
        row.update(_news_features(current_time, headlines))

        yield {
            "features": row,
            "current_time": current_time,
            "target_time": timestamps[i + 1],
            "base_close": current_close,
            "actual_close": next_close,
            # El modelo aprende el % de cambio al siguiente cierre, no el
            # precio absoluto: los árboles de LightGBM no pueden extrapolar
            # más allá del rango de precios visto en entrenamiento, y en una
            # serie que hace nuevos máximos (como un índice) eso produce
            # errores enormes. Prediciendo el retorno, el objetivo se queda
            # siempre en un rango acotado sin importar a qué nivel de precio
            # llegue el activo.
            "target_return": (next_close - current_close) / current_close,
        }


def build_feature_frame(asset, timeframe, lookback=100):
    """
    Arma (X, y) para entrenamiento: X = features disponibles en la vela i,
    y = % de cambio al cierre de la vela i+1 (lo que el modelo aprende).
    """
    rows, targets = [], []
    for sample in _iter_feature_samples(asset, timeframe, lookback):
        rows.append(sample["features"])
        targets.append(sample["target_return"])

    X = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    y = pd.Series(targets)
    valid_mask = X.notna().all(axis=1)
    return X[valid_mask].reset_index(drop=True), y[valid_mask].reset_index(drop=True)


def build_backtest_samples(asset, timeframe, lookback=100, n_points=30):
    """
    Últimos `n_points` puntos históricos con features + resultado real ya
    conocido (base_close, actual_close, target_time) — para simular el
    ciclo predicción/resolución sin depender de que el mercado esté
    abierto ahora mismo.
    """
    samples = [s for s in _iter_feature_samples(asset, timeframe, lookback) if X_is_valid(s["features"])]
    return samples[-n_points:]


def X_is_valid(feature_row):
    return all(v is not None and not pd.isna(v) for v in feature_row.values())


def build_inference_features(asset, timeframe, lookback=100):
    """Feature row para predecir la vela SIGUIENTE a la última disponible."""
    df = price_bars_dataframe(asset, timeframe)
    if len(df) < lookback:
        return None, None

    df = _add_technical_columns(df, lookback)
    current_time = df.index[-1]
    events = _load_economic_events(current_time - timedelta(hours=24), current_time + timedelta(hours=24))
    headlines = _load_news_headlines(current_time - timedelta(hours=6), current_time, asset.symbol)

    row = df.iloc[-1][["close", "rsi", "macd_line", "macd_signal", "atr", "sma_20",
                        "fib_position_pct", "fib_distance_pct"]].to_dict()
    row.update(_economic_event_features(current_time, events))
    row.update(_news_features(current_time, headlines))

    if any(pd.isna(v) for v in row.values()):
        return None, None

    return pd.DataFrame([row], columns=FEATURE_COLUMNS), current_time
