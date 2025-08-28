from django.contrib import admin
from .models import NewsFetchConfig

@admin.register(NewsFetchConfig)
class NewsFetchConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "interval_minutes", "is_enabled", "last_fetch_time")
    list_editable = ("interval_minutes", "is_enabled")
    list_display_links = ("id",)  # ✅ حدد رابط العنصر (بيكون قابل للنقر للدخول للتعديل الكامل)
    ordering = ("-last_fetch_time",)
