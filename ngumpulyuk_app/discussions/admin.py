from django.contrib import admin

from ngumpulyuk_app.discussions.models import Comment, Like, Thread

admin.site.register(Thread)
admin.site.register(Comment)
admin.site.register(Like)
