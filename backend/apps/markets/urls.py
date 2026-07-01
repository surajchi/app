from django.urls import path

from apps.markets.views import (
    ExchangeListView,
    HistoryView,
    InstrumentDetailView,
    InstrumentListView,
    MoversView,
    QuoteView,
)

app_name = "markets"

urlpatterns = [
    path("exchanges/", ExchangeListView.as_view(), name="exchanges"),
    path("movers/", MoversView.as_view(), name="movers"),
    path("instruments/", InstrumentListView.as_view(), name="instruments"),
    path("instruments/<str:symbol>/", InstrumentDetailView.as_view(), name="instrument-detail"),
    path("instruments/<str:symbol>/quote/", QuoteView.as_view(), name="instrument-quote"),
    path("instruments/<str:symbol>/history/", HistoryView.as_view(), name="instrument-history"),
]
