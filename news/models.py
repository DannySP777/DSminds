from django.db import models


class NewsItem(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField()
    source = models.CharField(max_length=120, blank=True)
    url = models.URLField(unique=True)
    published_at = models.DateTimeField()
    tickers = models.ManyToManyField(
        "scanner.Ticker", related_name="news_items", blank=True
    )

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class EconomicEvent(models.Model):
    IMPACT_CHOICES = [
        ("low", "Baja (1 estrella)"),
        ("medium", "Media (2 estrellas)"),
        ("high", "Alta (3 estrellas)"),
    ]
    STARS_BY_IMPACT = {"low": 1, "medium": 2, "high": 3}

    title = models.CharField(max_length=200)
    country = models.CharField(max_length=10, default="USD")
    event_time = models.DateTimeField()
    impact = models.CharField(max_length=10, choices=IMPACT_CHOICES)
    forecast = models.CharField(max_length=40, blank=True)
    previous = models.CharField(max_length=40, blank=True)
    actual = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["event_time"]
        unique_together = ("title", "event_time")

    def __str__(self):
        return f"{self.title} ({self.event_time:%d %b %H:%M})"

    @property
    def stars(self):
        return self.STARS_BY_IMPACT.get(self.impact, 1)

    @property
    def stars_display(self):
        n = self.stars
        return "★" * n + "☆" * (3 - n)
