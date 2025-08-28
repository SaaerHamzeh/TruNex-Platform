from django.contrib import admin
from .models import *



admin.site.register(NewsArticle)
admin.site.register(Favorite)
admin.site.register(Interest)
admin.site.register(UserInterest)
admin.site.register(Note)


# ✅ لإدارة روابط الأقسام داخل مصدر الأخبار
class NewsSourceSectionURLInline(admin.TabularInline):
    model = NewsSourceSectionURL
    extra = 1


class NewsSourceAdmin(admin.ModelAdmin):
    list_display = [
        "news_source_name",
        "news_source_method",
        "news_source_language",
        "fetch_limit",
        "fetch_interval_minutes",
    ]
    inlines = [NewsSourceSectionURLInline]


admin.site.register(NewsSource, NewsSourceAdmin)  # 👈 هاد بس خلي


