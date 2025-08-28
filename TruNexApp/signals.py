# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .models import NewsSource
from TruNexApp.tasks import scheduled_fetch_news
from django.utils import timezone


# @receiver(post_save, sender=NewsSource)
# def update_celery_interval(sender, instance, **kwargs):


#     source = NewsSource.objects.first()
#     interval_minutes = source.fetch_interval_minutes if source else 10

#     schedule, created = IntervalSchedule.objects.get_or_create(
#         every=interval_minutes,
#         period=IntervalSchedule.MINUTES,
#     )

#     PeriodicTask.objects.update_or_create(
#         name="جلب الأخبار تلقائياً",
#         defaults={
#             "interval": schedule,
#             "task": "TruNexApp.tasks.scheduled_fetch_news",
#             "start_time": timezone.now(),
#         },
#     )

def update_celery_interval(sender, instance, **kwargs):
    source = NewsSource.objects.first()
    interval_minutes = source.fetch_interval_minutes if source else 10

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=interval_minutes,
        period=IntervalSchedule.MINUTES,
    )

    # 🟡 لا تغير حالة التفعيل! احتفظ بالحالة الموجودة حاليًا
    existing_task = PeriodicTask.objects.filter(name="جلب الأخبار تلقائياً").first()
    is_enabled = existing_task.enabled if existing_task else True

    PeriodicTask.objects.update_or_create(
        name="جلب الأخبار تلقائياً",
        defaults={
            "interval": schedule,
            "task": "TruNexApp.tasks.scheduled_fetch_news",
            "enabled": is_enabled,
        },
    )