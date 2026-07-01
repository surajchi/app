from django.urls import path

from apps.news.views import (
    NewsCategoryListView,
    NewsDetailView,
    NewsListView,
    NewsSearchView,
    NewsTrendingView,
)

app_name = "news"

urlpatterns = [
    path("", NewsListView.as_view(), name="feed"),
    path("search/", NewsSearchView.as_view(), name="search"),
    path("trending/", NewsTrendingView.as_view(), name="trending"),
    path("categories/", NewsCategoryListView.as_view(), name="categories"),
    path("<uuid:id>/", NewsDetailView.as_view(), name="detail"),
]
