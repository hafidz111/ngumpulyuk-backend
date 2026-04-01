from django.contrib import admin

from ngumpulyuk_app.communities.models import Community, CommunityMember

admin.site.register(Community)
admin.site.register(CommunityMember)
