from django.contrib import admin

from .models import EconomicEvent, NewsItem


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published_at")
    list_filter = ("tickers",)
    search_fields = ("title", "source")
    filter_horizontal = ("tickers",)


@admin.register(EconomicEvent)
class EconomicEventAdmin(admin.ModelAdmin):
    list_display = ("title", "country", "event_time", "impact", "forecast", "previous", "actual")
    list_filter = ("impact", "country")
    search_fields = ("title",)
