import factory
from django.utils import timezone

from apps.news.models import NewsArticle, NewsCategory


class NewsCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsCategory
        django_get_or_create = ("slug",)

    slug = "markets"
    name = "Markets"


class NewsArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewsArticle

    source = "synthetic"
    source_url = factory.Sequence(lambda n: f"https://news.example/a/{n}")
    url_hash = factory.Sequence(lambda n: f"{n:064d}")
    simhash = factory.Sequence(lambda n: n + 1)
    title = "Test headline"
    body = "Test body"
    published_at = factory.LazyFunction(timezone.now)
    impact_score = 10
