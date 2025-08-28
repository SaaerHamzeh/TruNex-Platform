# from celery import shared_task
# import traceback


# @shared_task(name="TruNexApp.tasks.scheduled_fetch_news")
# def scheduled_fetch_news():
#     with open("celery_log.txt", "a", encoding="utf-8") as f:
#         f.write("🛰️ بدأ تنفيذ المهمة التلقائية...\n")

#     try:
#         from TruNexApp.news_fetchers import fetch_and_store_news

#         with open("celery_log.txt", "a", encoding="utf-8") as f:
#             f.write("📦 استيراد fetch_and_store_news...\n")

#         result = fetch_and_store_news()
#         with open("celery_log.txt", "a", encoding="utf-8") as f:
#             f.write(f"✅ تم التنفيذ! النتيجة: {result}\n")

#     except Exception as e:
#         import traceback

#         with open("celery_log.txt", "a", encoding="utf-8") as f:
#             f.write(f"❌ خطأ أثناء التنفيذ:\n{traceback.format_exc()}\n")

from celery import shared_task
import traceback


@shared_task(name="TruNexApp.tasks.scheduled_fetch_news")
def scheduled_fetch_news():
    from django_celery_beat.models import PeriodicTask

    # ✅ تحقق ما إذا كانت المهمة مفعّلة قبل التنفيذ
    task = PeriodicTask.objects.filter(name="جلب الأخبار تلقائياً").first()
    if task and not task.enabled:
        with open("celery_log.txt", "a", encoding="utf-8") as f:
            f.write("🚫 المهمة موقوفة، تم تجاهل التنفيذ.\n")
        return  # ⛔ لا تنفذ إذا كانت غير مفعلة

    with open("celery_log.txt", "a", encoding="utf-8") as f:
        f.write("🛰️ بدأ تنفيذ المهمة التلقائية...\n")

    try:
        from TruNexApp.news_fetchers import fetch_and_store_news

        with open("celery_log.txt", "a", encoding="utf-8") as f:
            f.write("📦 استيراد fetch_and_store_news...\n")

        result = fetch_and_store_news()
        with open("celery_log.txt", "a", encoding="utf-8") as f:
            f.write(f"✅ تم التنفيذ! النتيجة: {result}\n")

    except Exception as e:
        with open("celery_log.txt", "a", encoding="utf-8") as f:
            f.write(f"❌ خطأ أثناء التنفيذ:\n{traceback.format_exc()}\n")
