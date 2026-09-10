from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="scanner-home"),
    path("buscar/", views.ticker_search, name="ticker-search"),
    path("accion/<str:symbol>/mini/", views.ticker_mini_chart, name="ticker-mini-chart"),
    path("accion/<str:symbol>/panel-grafica/", views.ticker_chart_panel, name="ticker-chart-panel"),
    path("accion/<str:symbol>/panel-indicadores/", views.ticker_indicators_panel, name="ticker-indicators-panel"),
    path("accion/<str:symbol>/", views.ticker_detail, name="ticker-detail"),
]
