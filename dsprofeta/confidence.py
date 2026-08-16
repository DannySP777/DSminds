"""
Indicador de confianza de la predicción: combina el error histórico del
modelo en entrenamiento (MAE/RMSE del holdout, ver ModelRun) con su track
record real sobre predicciones ya resueltas (incluyendo las del
backtest), y calcula qué tan seguido acierta la DIRECCIÓN del movimiento
(sube/baja) — que es lo que más importa para decidir si confiar en la
predicción, más que el error absoluto en precio.
"""
from config.translations import get_translations

from .models import ModelRun, PriceBar, Prediction

# Reutiliza los mismos colores que el gauge de fundamentales del scanner
# (templates/partials/gauge.html + .gauge-dot--* en style.css).
LEVEL_CSS_CLASS = {"high": "good", "medium": "warning", "low": "bad", "unknown": "unknown"}


def _level_labels(T):
    return {"high": T["dsp_level_high"], "medium": T["dsp_level_medium"], "low": T["dsp_level_low"], "unknown": T["dsp_level_unknown"]}


def compute_confidence(asset, timeframe, lookback_predictions=100, lang="es"):
    T = get_translations(lang)
    level_labels = _level_labels(T)
    run = ModelRun.objects.filter(asset=asset, timeframe=timeframe, is_active=True).first()
    resolved = list(
        Prediction.objects.filter(asset=asset, timeframe=timeframe, actual_close__isnull=False)
        .order_by("-target_time")[:lookback_predictions]
    )

    if not resolved:
        return {
            "available": False, "run": run, "level": "unknown",
            "label": level_labels["unknown"], "css_level": LEVEL_CSS_CLASS["unknown"],
        }

    errors_pct = []
    direction_hits, direction_total = 0, 0

    for prediction in resolved:
        actual = float(prediction.actual_close)
        predicted = float(prediction.predicted_close)
        if actual:
            errors_pct.append(abs(actual - predicted) / actual * 100)

        # La vela base es la última disponible antes de target_time. No se
        # puede asumir timestamp == target_time - delta porque predict_next
        # adelanta target_time cuando cae en fin de semana (ver
        # ml._skip_weekend) — la resta ya no da la vela real en ese caso.
        base_bar = (
            PriceBar.objects.filter(
                asset=asset, timeframe=timeframe, timestamp__lt=prediction.target_time,
            )
            .order_by("-timestamp")
            .first()
        )
        if base_bar is None:
            continue
        base_close = float(base_bar.close)
        predicted_direction = predicted - base_close
        actual_direction = actual - base_close
        if predicted_direction == 0 or actual_direction == 0:
            continue
        direction_total += 1
        if (predicted_direction > 0) == (actual_direction > 0):
            direction_hits += 1

    mean_error_pct = sum(errors_pct) / len(errors_pct) if errors_pct else None
    direction_accuracy = (direction_hits / direction_total * 100) if direction_total else None
    level = _confidence_level(mean_error_pct, direction_accuracy)

    return {
        "available": True,
        "run": run,
        "n_resolved": len(resolved),
        "n_with_direction": direction_total,
        "mean_error_pct": round(mean_error_pct, 3) if mean_error_pct is not None else None,
        "direction_accuracy": round(direction_accuracy, 1) if direction_accuracy is not None else None,
        "level": level,
        "label": level_labels[level],
        "css_level": LEVEL_CSS_CLASS[level],
    }


def _confidence_level(mean_error_pct, direction_accuracy):
    if mean_error_pct is None or direction_accuracy is None:
        return "unknown"
    if mean_error_pct < 1.0 and direction_accuracy >= 60:
        return "high"
    if mean_error_pct < 3.0 and direction_accuracy >= 50:
        return "medium"
    return "low"
