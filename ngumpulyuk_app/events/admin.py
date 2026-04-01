from django.contrib import admin

from ngumpulyuk_app.events.models import Event, EventParticipant, EventTag

admin.site.register(Event)
admin.site.register(EventParticipant)
admin.site.register(EventTag)
