from django.urls import path

from apps.ai.views import (
    ForecastView,
    ModelsView,
    RecommendationsView,
    TechnicalView,
)

app_name = "ai"

urlpatterns = [
    path("forecast/<str:symbol>/", ForecastView.as_view(), name="forecast"),
    path("technical/<str:symbol>/", TechnicalView.as_view(), name="technical"),
    path("recommendations/", RecommendationsView.as_view(), name="recommendations"),
    path("models/", ModelsView.as_view(), name="models"),
]
