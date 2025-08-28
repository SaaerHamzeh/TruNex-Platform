from django.db import models


class NewsFetchConfig(models.Model):
    interval_minutes = models.IntegerField(
        default=10, help_text="عدد الدقائق بين كل جلب تلقائي"
    )
    is_enabled = models.BooleanField(
        default=True, help_text="تفعيل أو تعطيل الجلب التلقائي"
    )
    last_fetch_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"⏱️ كل {self.interval_minutes} دقيقة - {'✅ مفعل' if self.is_enabled else '⛔ متوقف'}"
