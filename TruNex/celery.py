from __future__ import absolute_import
import os
from celery import Celery

# إعدادات Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TruNex.settings")

# تعريف التطبيق
app = Celery("TruNex")

# تحميل الإعدادات من Django
app.config_from_object("django.conf:settings", namespace="CELERY")

# اكتشاف المهام تلقائيًا من كل التطبيقات
app.autodiscover_tasks()

# ✅ إجبار Celery Beat على استخدام قاعدة البيانات بدل الملف المؤقت
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
