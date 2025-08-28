

from django.apps import AppConfig

class TrunexappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "TruNexApp"

    def ready(self):
        import TruNexApp.tasks  # ✅ هذا السطر مهم جدًا
