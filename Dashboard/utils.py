from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.utils import timezone
from .models import NewsFetchConfig
from TruNexApp.tasks import scheduled_fetch_news
from TruNexApp.models import NewsSource


def apply_fetch_config():
    config, _ = NewsFetchConfig.objects.get_or_create(id=1)

    print(
        f"🔄 Applying config: interval={config.interval_minutes}, enabled={config.is_enabled}"
    )

    # تحديث جميع المصادر
    NewsSource.objects.update(fetch_interval_minutes=config.interval_minutes)

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=config.interval_minutes,
        period=IntervalSchedule.MINUTES,
    )

    task, created = PeriodicTask.objects.update_or_create(
        name="جلب الأخبار تلقائياً",
        defaults={
            "interval": schedule,
            "task": "TruNexApp.tasks.scheduled_fetch_news",  
            "enabled": config.is_enabled,
        },
    )

    print(f"✅ PeriodicTask {'created' if created else 'updated'}: {task}")


def toggle_fetch_server(state: bool):
    """تشغيل أو إيقاف الجلب التلقائي"""
    config, _ = NewsFetchConfig.objects.get_or_create(id=1)
    config.is_enabled = state
    config.save()
    apply_fetch_config()


def manual_fetch(triggered_by_view=False):
    if not triggered_by_view:
        print("⛔ manual_fetch() called without permission! Ignoring.")
        return

    from django.core.cache import cache
    if cache.get("fetching_status") == "running":
        print("⛔ Already running, skipping.")
        return

    print("🚀 manual_fetch() executed!")
    task = scheduled_fetch_news.delay()
    print(f"✅ Task ID: {task.id}")

    config, _ = NewsFetchConfig.objects.get_or_create(id=1)
    config.last_fetch_time = timezone.now()
    config.save()
