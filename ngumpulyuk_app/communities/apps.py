from django.apps import AppConfig


class CommunitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ngumpulyuk_app.communities"
    label = "communities"
    verbose_name = "Communities"

    def ready(self):
        from ngumpulyuk_app.communities import signals  # noqa: F401
