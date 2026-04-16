from django.contrib import admin

from ngumpulyuk_app.notifications.models import BlastNotificationAudit, Notification, PushDevice

admin.site.register(Notification)
admin.site.register(PushDevice)
admin.site.register(BlastNotificationAudit)
