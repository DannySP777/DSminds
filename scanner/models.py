from django.db import models


class Ticker(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=120, blank=True)
    sector = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)
    # True para tickers agregados por un visitante desde el buscador del
    # scanner (ver scanner/views.py:add_ticker) — se muestran siempre
    # fijados arriba de la tabla, sin importar la fecha del scan diario
    # por lotes ni los filtros activos.
    added_manually = models.BooleanField(default=False)
    added_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return self.symbol


class ScanResult(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="results")
    date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    rsi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    relative_volume = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    breakout = models.BooleanField(default=False)
    ma200 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    above_ma200 = models.BooleanField(default=False)
    atr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    relative_strength = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    macd = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    macd_signal = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    # True si la línea MACD está por encima de su señal y ambas por
    # encima de cero (cruce alcista con tendencia de fondo confirmada).
    macd_bullish = models.BooleanField(default=False)
    current_ratio = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    target_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    market_cap_display = models.CharField(max_length=20, blank=True)
    trailing_pe = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    peg_ratio = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    debt_to_equity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exchange = models.CharField(max_length=40, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date", "-score"]
        unique_together = ("ticker", "date")

    def __str__(self):
        return f"{self.ticker.symbol} — {self.date}"

    @property
    def target_upside_pct(self):
        if self.target_price and self.price:
            return round(float(self.target_price) / float(self.price) * 100 - 100, 1)
        return None
