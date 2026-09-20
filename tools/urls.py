from django.urls import path

from . import views

urlpatterns = [
    path("", views.trading_analysis, name="trading-analysis"),
    # La antigua portada (Top 10 de estrategias + calculadoras) vive acá; se
    # conserva el nombre "tools-index" porque las calculadoras enlazan a él.
    path("estrategias/", views.tools_index, name="tools-index"),
    path("interes-compuesto/", views.compound_interest, name="tool-compound-interest"),
    path("riesgo-beneficio/", views.risk_reward, name="tool-risk-reward"),
    path("fair-value-gap/", views.fair_value_gap, name="tool-fair-value-gap"),
]
