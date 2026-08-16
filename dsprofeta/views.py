from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from config.translations import DEFAULT_LANG, SUPPORTED_LANGS, get_translations

from .charts import (
    DEFAULT_HISTORY_BARS,
    build_macd_chart,
    build_prediction_chart,
    build_rsi_chart,
    clamp_history_bars,
    invalidate_prediction_chart,
)
from .commentary import interpret_macd, interpret_rsi, upcoming_economic_events
from .confidence import compute_confidence
from .dial_gauges import compute_overall_score, direction_dial
from .ml import predict_next
from .models import Asset, Prediction, PriceBar

TIMEFRAME_LABEL_KEYS = {
    "15m": "dsp_timeframe_15m", "1h": "dsp_timeframe_1h", "4h": "dsp_timeframe_4h",
    "1d": "dsp_timeframe_1d", "1w": "dsp_timeframe_1w",
}
ASSET_NAME_KEYS = {
    "NDX100": "dsp_asset_ndx100", "GOLD": "dsp_asset_gold",
    "EURUSD": "dsp_asset_eurusd", "SPX500": "dsp_asset_spx500",
}
DEFAULT_TIMEFRAME = PriceBar.Timeframe.D1
HISTORY_BAR_CHOICES = [20, 50, 100]


def _get_lang(request):
    lang = request.COOKIES.get("site_lang", DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def _localized_assets(assets, T):
    return [
        {"symbol": a.symbol, "display_name": T.get(ASSET_NAME_KEYS.get(a.symbol), a.display_name)}
        for a in assets
    ]


def _format_chart_captions(chart, T):
    if chart and chart.get("error") is None:
        chart["caption"] = T["dsp_chart_caption"].format(bars=chart["history_bars"])
        chart["stats_text"] = T["dsp_chart_stats"].format(
            n_predictions=chart["n_predictions"], n_resolved=chart["n_resolved"],
        )
        chart["mae_text"] = T["dsp_chart_mae"].format(mae=chart["mae"]) if chart["mae"] else None
    return chart


def predictor_home(request):
    lang = _get_lang(request)
    T = get_translations(lang)

    assets = Asset.objects.filter(is_active=True)
    default_symbol = assets.first().symbol if assets.exists() else ""
    asset_symbol = request.GET.get("asset") or default_symbol
    timeframe = request.GET.get("timeframe", DEFAULT_TIMEFRAME)
    if timeframe not in TIMEFRAME_LABEL_KEYS:
        timeframe = DEFAULT_TIMEFRAME
    history_bars = clamp_history_bars(request.GET.get("history_bars", DEFAULT_HISTORY_BARS))

    asset = assets.filter(symbol=asset_symbol).first()
    chart = build_prediction_chart(asset, timeframe, history_bars, lang) if asset else None
    rsi_chart = build_rsi_chart(asset, timeframe, history_bars, lang) if asset else None
    macd_chart = build_macd_chart(asset, timeframe, history_bars, lang) if asset else None
    confidence = compute_confidence(asset, timeframe, lang=lang) if asset else None
    rsi_comment = interpret_rsi(rsi_chart["last_rsi"] if rsi_chart else None, lang=lang)
    macd_comment = interpret_macd(
        macd_chart["last_macd_line"] if macd_chart else None,
        macd_chart["last_macd_signal"] if macd_chart else None,
        chart["last_close"] if chart else None,
        lang=lang,
    )
    upcoming_events = upcoming_economic_events(lang=lang)

    latest_prediction = (
        Prediction.objects.filter(asset=asset, timeframe=timeframe).order_by("-generated_at").first()
        if asset else None
    )
    overall_score = compute_overall_score(
        rsi_comment["level"], macd_comment["level"],
        latest_prediction.predicted_close if latest_prediction else None,
        chart["last_close"] if chart else None,
    )

    chart = _format_chart_captions(chart, T)

    if confidence and confidence.get("available"):
        confidence_label_text = T["dsp_confidence_label"].format(label=confidence["label"])
    else:
        confidence_label_text = None

    return render(request, "dsprofeta/home.html", {
        "assets": _localized_assets(assets, T),
        "selected_asset": asset_symbol,
        "timeframes": [(value, T[key]) for value, key in TIMEFRAME_LABEL_KEYS.items()],
        "selected_timeframe": timeframe,
        "history_bar_choices": HISTORY_BAR_CHOICES,
        "selected_history_bars": history_bars,
        "chart": chart,
        "rsi_chart": rsi_chart,
        "macd_chart": macd_chart,
        "confidence": confidence,
        "rsi_comment": rsi_comment,
        "macd_comment": macd_comment,
        "upcoming_events": upcoming_events,
        "direction_dial": direction_dial(overall_score, lang=lang),
        "confidence_label_text": confidence_label_text,
    })


def predict(request):
    if request.method != "POST":
        return redirect("predictor-home")

    lang = _get_lang(request)
    T = get_translations(lang)

    asset_symbol = request.POST.get("asset", "")
    timeframe = request.POST.get("timeframe", "")
    history_bars = clamp_history_bars(request.POST.get("history_bars", DEFAULT_HISTORY_BARS))
    asset = Asset.objects.filter(symbol=asset_symbol, is_active=True).first()

    if not asset or timeframe not in TIMEFRAME_LABEL_KEYS:
        messages.error(request, T["dsp_select_asset_timeframe"])
        return redirect("predictor-home")

    try:
        prediction = predict_next(asset, timeframe)
        invalidate_prediction_chart(asset, timeframe, history_bars)
        messages.success(request, T["dsp_prediction_saved"].format(
            symbol=asset.symbol, timeframe=T[TIMEFRAME_LABEL_KEYS[timeframe]],
            value=prediction.predicted_close, time=f"{prediction.target_time:%Y-%m-%d %H:%M}",
        ))
    except ValueError as exc:
        messages.error(request, str(exc))

    redirect_url = (
        f"{reverse('predictor-home')}?asset={asset_symbol}&timeframe={timeframe}&history_bars={history_bars}"
    )
    return redirect(redirect_url)


def prediction_chart_panel(request, symbol, timeframe):
    """Fragmento AJAX: solo el panel de gráfica (velas + predicción)."""
    lang = _get_lang(request)
    T = get_translations(lang)
    history_bars = clamp_history_bars(request.GET.get("history_bars", DEFAULT_HISTORY_BARS))
    asset = Asset.objects.filter(symbol=symbol).first()
    chart = build_prediction_chart(asset, timeframe, history_bars, lang) if asset else None
    chart = _format_chart_captions(chart, T)
    return render(request, "dsprofeta/partials/chart_panel.html", {
        "chart": chart,
        "symbol": symbol,
        "timeframe": timeframe,
    })
