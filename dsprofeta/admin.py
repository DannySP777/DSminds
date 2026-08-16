from django.contrib import admin

from .models import Asset, EconomicEvent, ModelRun, NewsHeadline, PriceBar, Prediction


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "display_name", "yfinance_symbol", "asset_class", "is_active")
    search_fields = ("symbol", "display_name")


@admin.register(PriceBar)
class PriceBarAdmin(admin.ModelAdmin):
    list_display = ("asset", "timeframe", "timestamp", "open", "high", "low", "close", "volume")
    list_filter = ("asset", "timeframe")
    search_fields = ("asset__symbol",)


@admin.register(EconomicEvent)
class EconomicEventAdmin(admin.ModelAdmin):
    list_display = ("title", "country", "impact", "event_time", "actual", "forecast", "previous")
    list_filter = ("impact", "country")
    search_fields = ("title", "country")


@admin.register(NewsHeadline)
class NewsHeadlineAdmin(admin.ModelAdmin):
    list_display = ("headline", "source", "published_at", "related_symbols")
    search_fields = ("headline", "related_symbols")


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "asset", "timeframe", "generated_at", "target_time",
        "predicted_close", "actual_close", "error_pct", "model_version",
    )
    list_filter = ("asset", "timeframe", "model_version")
    search_fields = ("asset__symbol",)


@admin.register(ModelRun)
class ModelRunAdmin(admin.ModelAdmin):
    list_display = ("asset", "timeframe", "version", "trained_at", "mae", "rmse", "n_samples", "is_active")
    list_filter = ("asset", "timeframe", "is_active")
