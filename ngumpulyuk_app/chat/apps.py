from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ngumpulyuk_app.chat"
    label = "chat"
    verbose_name = "Chat assistant"
