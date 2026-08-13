from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="scanner-home"),
    path("buscar/", views.ticker_search, name="ticker-search"),
    path("buscar/sugerencias/", views.ticker_autocomplete, name="ticker-autocomplete"),
    path("accion/agregar/", views.add_ticker, name="add-ticker"),
    path("accion/<str:symbol>/quitar/", views.remove_ticker, name="remove-ticker"),
    path("accion/<str:symbol>/mini/", views.ticker_mini_chart, name="ticker-mini-chart"),
    path("accion/<str:symbol>/panel-grafica/", views.ticker_chart_panel, name="ticker-chart-panel"),
    path("accion/<str:symbol>/panel-indicadores/", views.ticker_indicators_panel, name="ticker-indicators-panel"),
    path("accion/<str:symbol>/", views.ticker_detail, name="ticker-detail"),
]
