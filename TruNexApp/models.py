from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone


class NewsSource(models.Model):
    news_source_id = models.AutoField(primary_key=True)
    news_source_name = models.CharField(max_length=100)
    news_source_url = models.TextField()
    news_source_method = models.CharField(
        max_length=20,
        choices=[("api", "API"), ("rss", "RSS"), ("scraper", "Scraper")],
        default="api",
    )
    news_source_language = models.CharField(max_length=5, default="en")

    description = models.TextField(blank=True, null=True)
    fetch_limit = models.IntegerField(
        default=10, help_text="عدد المقالات المطلوبة من المصدر"
    )
    fetch_interval_minutes = models.IntegerField(
        default=60, help_text="الفاصل الزمني بالدقائق بين كل طلب تلقائي"
    )
    last_fetched_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" {self.news_source_name} - {self.news_source_url}"


class NewsSourceSectionURL(models.Model):
    source = models.ForeignKey(
        "NewsSource", on_delete=models.CASCADE, related_name="section_urls"
    )
    section_type = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="نوع القسم (مثل: politics, sports، ويمكن تركه فارغ)",
    )
    section_region = models.CharField(
        max_length=10,
        choices=[
            ("syria", "syria"),
            ("arab", "arab"),
            ("world", "world"),
        ],
        blank=True,
        null=True,
        help_text="النطاق الجغرافي: syria أو arab أو world (يمكن تركه فارغ)",
    )
    section_url = models.TextField()

    def __str__(self):
        region = self.section_region or "no-region"
        type_ = self.section_type or "no-type"
        return f"{self.source.news_source_name} - {type_} - {region}"


class Interest(models.Model):
    interest_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"Interest: {self.name}"


class NewsArticle(models.Model):
    news_article_id = models.AutoField(primary_key=True)
    news_article_source = models.ForeignKey(NewsSource, on_delete=models.CASCADE)
    news_article_url = models.URLField(null=True, blank=True)
    news_article_type = models.CharField(max_length=50, null=True, blank=True)
    news_article_is_fake = models.BooleanField(null=True, blank=True)
    news_article_fake_score = models.FloatField(null=True, blank=True)

    REGION_CHOICES = [
        ("syria", "syria"),
        ("arab", "arab"),
        ("world", "world"),
    ]
    news_article_region = models.CharField(
        max_length=10, choices=REGION_CHOICES, default="arab"
    )
    news_article_title = models.CharField(max_length=250)
    news_article_content = models.TextField()
    news_article_keywords = models.TextField()

    news_article_category = models.ForeignKey(
        Interest, on_delete=models.SET_NULL, null=True, blank=True
    )

    # ✅ الحقول الجديدة:
    news_article_image = models.URLField(null=True, blank=True)  # رابط صورة
    news_article_published_at = models.DateTimeField(
        null=True, blank=True
    )  # تاريخ النشر
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.news_article_source} - {self.news_article_title}"


# ✅ مفضلات المستخدم
class Favorite(models.Model):
    favorite_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    news_article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "news_article")

    def __str__(self):
        return f"{self.user.username}'s favorite: Article {self.news_article.news_article_id}"


# ✅ اهتمامات المستخدم (User's preferences)
class UserInterest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "interest")

    def __str__(self):
        return f"{self.user.username}'s interest: {self.interest.name}"


# ________________________________________________________
class Note(models.Model):
    description = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
