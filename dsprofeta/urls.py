from django.urls import path

from . import views

urlpatterns = [
    path("", views.predictor_home, name="predictor-home"),
    path("predecir/", views.predict, name="predictor-predict"),
    path("<str:symbol>/<str:timeframe>/panel-grafica/", views.prediction_chart_panel, name="predictor-chart-panel"),
]
