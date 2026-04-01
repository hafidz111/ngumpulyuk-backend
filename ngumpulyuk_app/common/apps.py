from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ngumpulyuk_app.common"
    label = "common"
    verbose_name = "Common (shared utilities)"
