"""
Entrenamiento e inferencia del predictor de DSprofeta (LightGBM).
"""
import logging
from datetime import timedelta
from pathlib import Path

import joblib
import pandas as pd
from django.utils import timezone as dj_timezone
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .features import FEATURE_COLUMNS, build_feature_frame, build_inference_features
from .models import ModelRun, Prediction

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent / "trained_models"
MODELS_DIR.mkdir(exist_ok=True)

TIMEFRAME_DELTAS = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
    "1w": timedelta(weeks=1),
}

MIN_TRAINING_SAMPLES = 30


def _model_path(asset, timeframe, version):
    return MODELS_DIR / f"{asset.symbol}_{timeframe}_{version}.joblib"


def _skip_weekend(dt):
    """
    El mercado no opera sábado ni domingo (charts.py oculta ese rango con
    un rangebreak para no mostrar huecos), así que un target_time que caiga
    ahí nunca se ve dibujado aunque esté guardado correctamente. Lo
    adelantamos al lunes a la misma hora — el próximo momento en que
    realmente puede existir una vela nueva.
    """
    if dt.weekday() == 5:  # sábado
        return dt + timedelta(days=2)
    if dt.weekday() == 6:  # domingo
        return dt + timedelta(days=1)
    return dt


def train(asset, timeframe, test_size=0.2):
    """
    Entrena un modelo nuevo para (asset, timeframe) con el historial
    disponible en PriceBar (incluyendo predicciones ya resueltas, que
    se van sumando al historial con el tiempo — así el modelo mejora
    con cada reentreno). Split temporal (nunca aleatorio): la parte
    de test es siempre posterior a la de entrenamiento.
    """
    from lightgbm import LGBMRegressor

    X, y = build_feature_frame(asset, timeframe)
    if len(X) < MIN_TRAINING_SAMPLES:
        raise ValueError(
            f"No hay suficiente historial para entrenar {asset.symbol} ({timeframe}): "
            f"{len(X)} muestras (mínimo {MIN_TRAINING_SAMPLES}). "
            f"Corre sync_prediction_prices primero."
        )

    # y es el % de cambio al siguiente cierre (ver features.py). Se entrena
    # y evalúa en ese espacio, y se reconstruye a precio solo para reportar
    # MAE/RMSE en unidades que tengan sentido (dólares/puntos, no %).
    split_idx = int(len(X) * (1 - test_size))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = LGBMRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42, verbosity=-1)
    model.fit(X_train, y_train)

    if len(X_test):
        predicted_returns = model.predict(X_test)
        base_close = X_test["close"].to_numpy()
        predicted_prices = base_close * (1 + predicted_returns)
        actual_prices = base_close * (1 + y_test.to_numpy())
        mae = mean_absolute_error(actual_prices, predicted_prices)
        rmse = mean_squared_error(actual_prices, predicted_prices) ** 0.5
    else:
        mae = rmse = 0.0

    version = dj_timezone.now().strftime("%Y%m%d%H%M%S")
    joblib.dump(model, _model_path(asset, timeframe, version))

    ModelRun.objects.filter(asset=asset, timeframe=timeframe, is_active=True).update(is_active=False)
    run = ModelRun.objects.create(
        asset=asset, timeframe=timeframe, version=version,
        mae=round(mae, 6), rmse=round(rmse, 6), n_samples=len(X), is_active=True,
    )
    logger.info(
        "Entrenado %s (%s) v%s — MAE=%.4f RMSE=%.4f n=%d",
        asset.symbol, timeframe, version, mae, rmse, len(X),
    )
    return run


def _load_active_run(asset, timeframe):
    run = ModelRun.objects.filter(asset=asset, timeframe=timeframe, is_active=True).first()
    if run is None:
        raise ValueError(
            f"No hay un modelo entrenado para {asset.symbol} ({timeframe}). "
            f"Corre train_predictors primero."
        )
    return run


def predict_next(asset, timeframe):
    run = _load_active_run(asset, timeframe)
    model = joblib.load(_model_path(asset, timeframe, run.version))
    X, current_time = build_inference_features(asset, timeframe)
    if X is None:
        raise ValueError(f"No hay suficientes datos recientes para predecir {asset.symbol} ({timeframe}).")

    predicted_return = float(model.predict(X)[0])
    current_close = float(X["close"].iloc[0])
    predicted_close = current_close * (1 + predicted_return)
    target_time = _skip_weekend(current_time + TIMEFRAME_DELTAS[timeframe])

    return Prediction.objects.create(
        asset=asset, timeframe=timeframe, target_time=target_time,
        predicted_close=round(predicted_close, 5), model_version=run.version,
    )


def predict_from_features(asset, timeframe, feature_row):
    """
    Corre el modelo activo sobre un feature row ya armado (no vuelve a
    leer PriceBar) — usado por el backtest (management/commands/backtest_predictions.py)
    para simular predicciones sobre velas históricas ya conocidas.
    Devuelve (predicted_return, model_version).
    """
    run = _load_active_run(asset, timeframe)
    model = joblib.load(_model_path(asset, timeframe, run.version))
    X = pd.DataFrame([feature_row], columns=FEATURE_COLUMNS)
    predicted_return = float(model.predict(X)[0])
    return predicted_return, run.version
