# ✅ news_fetchers.py - نسخة محدثة تدعم الجلب من الأقسام الفرعية لكل مصدر

from .models import NewsSource, NewsArticle
from .base import fetch_news_from_source
from datetime import datetime
from .scraper_fetcher import infer_article_type
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from TruNexApp.realtime_broadcast import push_log, push_countdown


# ______________________________________________
from .ai_models.llm_utils import (
    summarize_text_with_openrouter,
    detect_article_type_with_openrouter,
    detect_article_region_with_openrouter,
    detect_fake_news_score_with_openrouter,
)


def store_article(source, article, region=None, type=None):
    title = article["title"]
    if NewsArticle.objects.filter(
        news_article_title=title, news_article_source=source
    ).exists():
        return False  # المقال موجود مسبقًا

    # تخزين التلخيص من المودل
    original_content = article["content"]
    summarized = summarize_text_with_openrouter(original_content)

    # توقع نوع المقال
    detected_type = (
        detect_article_type_with_openrouter(article.get("content") or title)
        or type
        or article.get("type")
    )

    # توقع صحة المقال
    score = detect_fake_news_score_with_openrouter(original_content)
    score_percent = int(round(score * 100))

    # 🔎 تحديد الحالة
    if score_percent < 65:
        is_fake = False
    elif score_percent > 75:
        is_fake = True
    else:
        is_fake = None  # ⬅️ غير معروف

    # توقع المنطقة
    detected_region = detect_article_region_with_openrouter(
        article.get("content") or title
    ) or ("world" if source.news_source_method == "api" else "arab")

    NewsArticle.objects.create(
        news_article_source=source,
        news_article_title=title,
        # news_article_content=article["content"],
        news_article_content=summarized,
        news_article_type=detected_type,
        news_article_is_fake=is_fake,  # Boolean or None
        news_article_fake_score=score_percent,  # Int %
        news_article_region=detected_region,
        news_article_url=article.get("url"),
        news_article_keywords=article.get("keywords", ""),
        news_article_category=article.get("category"),
        news_article_image=article.get("image"),
        news_article_published_at=article.get("published_at"),
    )
    return True


def fetch_and_store_news(request=None):

    try:
        cache.set("fetching_status", "running", timeout=600)
        print("🟢 Running section-based fetch mode")

        sources = NewsSource.objects.all()
        # print(f"📦 Total sources: {sources.count()}")
        push_log(f"📦 Total sources: {sources.count()}")

        for source in sources:
            try:
                # print(
                #     f"\n🧭 Fetching from: {source.news_source_name} [{source.news_source_method.upper()}]"
                # )
                push_log(f"🧭 Fetching from: {source.news_source_name}")

                section_urls = source.section_urls.all()

                if section_urls.exists():
                    for section in section_urls:
                        print(
                            f"🌐 Section: {section.section_type or 'no-type'} | {section.section_url}"
                        )
                        try:
                            section_articles = fetch_news_from_source(
                                source, target=section
                            )

                            if source.fetch_limit > 0:
                                section_articles = section_articles[
                                    : source.fetch_limit
                                ]

                            for article in section_articles:
                                added = store_article(
                                    source,
                                    article,
                                    region=section.section_region,
                                    type=section.section_type,
                                )
                                if added:
                                    # print(f"📝 Stored: {article['title']}")
                                    push_log(f"📝 Stored: {article['title']}")

                        except Exception as e:
                            print(
                                f"⚠️ Error fetching section {section.section_url}: {e}"
                            )
                else:
                    # fallback إذا ما في أقسام
                    print("⚠️ No sections found, using main URL")
                    total_articles = fetch_news_from_source(source)

                    if source.fetch_limit > 0:
                        total_articles = total_articles[: source.fetch_limit]

                    for article in total_articles:
                        added = store_article(source, article)
                        if added:
                            print(f"📝 Stored: {article['title']}")
                            push_log(f"📝 Stored: {article['title']}")

                source.last_fetched_at = timezone.now()
                source.save()

            except Exception as e:
                import traceback

                print(f"❌ Error fetching from source {source.news_source_name}:")
                print(traceback.format_exc())

        print("✅ All fetching completed successfully.")
        source = NewsSource.objects.first()
        interval = source.fetch_interval_minutes
        next_time = timezone.now() + timedelta(minutes=interval)

        push_log("✅ تم الانتهاء من الجلب التلقائي")
        push_countdown(int(next_time.timestamp()))

    except Exception as e:
        import traceback

        print("🔥 CRITICAL ERROR in fetch_and_store_news:")
        print(traceback.format_exc())

    finally:
        cache.set("fetching_status", "idle", timeout=3600)
