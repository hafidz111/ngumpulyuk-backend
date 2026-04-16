from django.contrib import admin

from ngumpulyuk_app.notifications.models import Notification, PushDevice

admin.site.register(Notification)
admin.site.register(PushDevice)
