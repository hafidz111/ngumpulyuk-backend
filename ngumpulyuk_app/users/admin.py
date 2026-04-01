from django.contrib import admin

from ngumpulyuk_app.users.models import ActivityHistory, UserInterest, UserPreferences

admin.site.register(UserPreferences)
admin.site.register(UserInterest)
admin.site.register(ActivityHistory)
