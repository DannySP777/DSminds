from django.db import models


class Asset(models.Model):
    class AssetClass(models.TextChoices):
        INDEX = "index", "Índice"
        FOREX = "forex", "Forex"
        COMMODITY = "commodity", "Materia prima"

    symbol = models.CharField(max_length=20, unique=True)
    display_name = models.CharField(max_length=80)
    yfinance_symbol = models.CharField(max_length=20)
    asset_class = models.CharField(max_length=12, choices=AssetClass.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return self.symbol


class PriceBar(models.Model):
    class Timeframe(models.TextChoices):
        M15 = "15m", "15 minutos"
        H1 = "1h", "1 hora"
        H4 = "4h", "4 horas"
        D1 = "1d", "Diaria"
        W1 = "1w", "Semanal"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="bars")
    timeframe = models.CharField(max_length=3, choices=Timeframe.choices)
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=14, decimal_places=5)
    high = models.DecimalField(max_digits=14, decimal_places=5)
    low = models.DecimalField(max_digits=14, decimal_places=5)
    close = models.DecimalField(max_digits=14, decimal_places=5)
    volume = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        unique_together = ("asset", "timeframe", "timestamp")

    def __str__(self):
        return f"{self.asset.symbol} {self.timeframe} — {self.timestamp}"


class EconomicEvent(models.Model):
    class Impact(models.TextChoices):
        LOW = "low", "Bajo"
        MEDIUM = "medium", "Medio"
        HIGH = "high", "Alto"

    event_time = models.DateTimeField()
    country = models.CharField(max_length=10, blank=True)
    title = models.CharField(max_length=200)
    impact = models.CharField(max_length=6, choices=Impact.choices, default=Impact.LOW)
    actual = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    forecast = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    previous = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        ordering = ["-event_time"]
        unique_together = ("event_time", "title", "country")

    def __str__(self):
        return f"{self.title} ({self.country}) — {self.event_time}"


class NewsHeadline(models.Model):
    published_at = models.DateTimeField()
    headline = models.CharField(max_length=300)
    related_symbols = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.headline[:80]


class Prediction(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="predictions")
    timeframe = models.CharField(max_length=3, choices=PriceBar.Timeframe.choices)
    generated_at = models.DateTimeField(auto_now_add=True)
    target_time = models.DateTimeField()
    predicted_close = models.DecimalField(max_digits=14, decimal_places=5)
    model_version = models.CharField(max_length=40)
    actual_close = models.DecimalField(max_digits=14, decimal_places=5, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-generated_at"]

    def __str__(self):
        return f"{self.asset.symbol} {self.timeframe} → {self.target_time}"

    @property
    def error_pct(self):
        if self.actual_close is None:
            return None
        return round(float(self.actual_close - self.predicted_close) / float(self.actual_close) * 100, 3)


class ModelRun(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="model_runs")
    timeframe = models.CharField(max_length=3, choices=PriceBar.Timeframe.choices)
    version = models.CharField(max_length=40)
    trained_at = models.DateTimeField(auto_now_add=True)
    mae = models.DecimalField(max_digits=14, decimal_places=6)
    rmse = models.DecimalField(max_digits=14, decimal_places=6)
    n_samples = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)
    # El modelo entrenado (joblib) se guarda acá en vez de en disco: Railway
    # reconstruye el contenedor en cada deploy y borra el filesystem local,
    # así que un archivo en dsprofeta/trained_models/ desaparece con el
    # próximo push aunque la fila de ModelRun siga apuntando a esa versión.
    # La base de datos es lo único que persiste entre deploys.
    model_blob = models.BinaryField(null=True, blank=True)

    class Meta:
        ordering = ["-trained_at"]

    def __str__(self):
        return f"{self.asset.symbol} {self.timeframe} v{self.version}"
