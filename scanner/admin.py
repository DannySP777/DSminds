from django.contrib import admin

from .models import ScanResult, Ticker


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "sector", "is_active")
    search_fields = ("symbol", "name")


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = (
        "ticker", "date", "price", "rsi", "relative_volume", "breakout",
        "above_ma200", "atr", "relative_strength", "macd_bullish", "current_ratio",
        "target_price", "target_upside_pct", "market_cap_display", "trailing_pe",
        "peg_ratio", "debt_to_equity", "exchange", "score",
    )
    list_filter = ("date", "breakout", "above_ma200", "macd_bullish", "exchange")
    search_fields = ("ticker__symbol",)
