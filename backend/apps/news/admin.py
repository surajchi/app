from django.contrib import admin

from apps.news.models import NewsArticle, NewsCategory, NewsEntity, NewsSentiment


class NewsEntityInline(admin.TabularInline):
    model = NewsEntity
    extra = 0


class NewsSentimentInline(admin.StackedInline):
    model = NewsSentiment
    extra = 0


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "parent")
    search_fields = ("slug", "name")


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "category", "impact_score", "is_breaking", "published_at")
    list_filter = ("source", "is_breaking", "status", "category")
    search_fields = ("title", "body", "source_url")
    date_hierarchy = "published_at"
    inlines = (NewsSentimentInline, NewsEntityInline)
    readonly_fields = ("url_hash", "simhash")


@admin.register(NewsEntity)
class NewsEntityAdmin(admin.ModelAdmin):
    list_display = ("entity_text", "entity_type", "linked_kind", "linked_id")
    list_filter = ("entity_type", "linked_kind")
    search_fields = ("entity_text",)
