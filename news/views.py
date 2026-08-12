from django.shortcuts import render

from .models import EconomicEvent, NewsItem


def news_list(request):
    items = NewsItem.objects.prefetch_related("tickers").all()
    ticker_filter = request.GET.get("ticker", "").upper().strip()
    if ticker_filter:
        items = items.filter(tickers__symbol=ticker_filter)

    calendar_events = EconomicEvent.objects.order_by("event_time")

    return render(
        request,
        "news/list.html",
        {
            "items": items[:40],
            "ticker_filter": ticker_filter,
            "calendar_events": calendar_events,
        },
    )
